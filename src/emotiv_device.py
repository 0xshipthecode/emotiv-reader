
#
#  This class is responsible for:
#    - reading in the raw packet data from the /dev/eeg/encrypted device
#    - decrypting the signal (two 16-byte packets, ECB mode AES)
#    - queuing the decoded packets for buffer pull requests
#    - forwarding the packets to registered subscribers
#    - passing the packets to the EmotivDevice for updating
#

import string
import threading
import select
import traceback
import time

import Queue
from Crypto.Cipher import AES


from emotiv_data_packet import EmotivDataPacket, counter_to_sensor_id


class EmotivDevice:
    """
    This class is responsible for:
      - reading in the raw packet data from the /dev/eeg/encrypted device
      - decrypting the signal (two 16-byte packets, ECB mode AES)
      - queuing the decoded packets for buffer pull requests
      - forwarding the packets to registered subscribers
      - interpreting the packets to update the device state (battery, contact quality, gyro readouts)
    """


    def __init__(self, serial_num, in_dev_name = '/dev/eeg/encrypted'):
        """
        Initialize the Emotiv device with its serial number.
        """
        self.in_dev_name = in_dev_name

        # permanent objects
        self.packet_queue = Queue.Queue()
        self.setup_aes_cipher(serial_num)

        # setup state-dependent objects
        self.clear_state()


    def clear_state(self):
        """
        Clear state information in the headset.
        """
        self.gyro_x = None
        self.gyro_y = None
        self.battery = None
        self.cq = dict(zip(counter_to_sensor_id, [ 0.0 ] * 14))
        while not self.packet_queue.empty():
            self.packet_queue.get()
            self.packet_queue.task_done()
        self.subscribers = []
        self.stop_requested = False
        self.running = False
        self.reader = None
        self.packet_speed = 0.0


    def start_reader(self):
        """
        Start the reader thread.
        """
        # if already started, return immediately
        if self.running:
            return

        # construct a new reader & start it
        self.reader = threading.Thread(target = self.read_data)
        self.reader.start()


    def stop_reader(self):
        """
        Stop the reader thread.
        """
        if not self.running:
            return

        # request stop here
        self.stop_requested = True

        # wait for the reader thread to join
        self.reader.join()
        self.reader = None

        # the reader thread resets running & stop_requested flags


    def read_data(self):

        ts_buf = [ 0 ] * 128
        ts_ndx = 0

        # open the device, if unsuccesfull, return immediately
        try:
            f = open(self.in_dev_name, 'r')

            # we're only running if the file opened succesfully
            self.running = True

            # read until we are told to stop
            while not self.stop_requested:

                # wait until data is ready, if not continue (and check if stop is requested)
                ret = select.select([f], [], [], 0.1)
                if len(ret[0]) == 0:
                    self.packet_speed = 0.0
                    continue

                # read 32 bytes from the device
                enc_data = f.read(32)

                # record the packet incoming time
                ts_buf[ts_ndx] = time.time()
                rd_ndx = (ts_ndx + 1) % 128
                self.packet_speed = 128.0 / (ts_buf[ts_ndx] - ts_buf[rd_ndx])
                ts_ndx = (ts_ndx + 1) % 128
            
                # decrypt the data using the AES cipher (two 16 byte blocks)
                raw_data = self.aes.decrypt(enc_data[:16]) + self.aes.decrypt(enc_data[16:])

                # enqueue the packet
                packet = EmotivDataPacket(raw_data)
                self.packet_queue.put(packet)

                # forward the packet to subscribers
                for sub_callback in self.subscribers:
                    sub_callback(packet)

                # update the device state according to the packet
                if packet.battery:
                    self.battery = packet.battery

                # update gyros
                self.gyro_x, self.gyro_y = packet.gyro_x, packet.gyro_y

                #  update contact quality information
                if packet.cq_id is not None:
                    self.cq[packet.cq_id] = packet.cq_val

        except IOError as ioe:
#            print("Error in Device reader thread: %s, terminating." % ioe)
#            print(traceback.print_exc(ioe))
            pass

        finally:
            # reset flags
            self.running = False
            self.stop_requested = False

            # close device
            if f is not None:
                f.close()


    def setup_aes_cipher(self, sn):
        """
        This routine is again taken from emokit.py, specialized
        for only the research headset and modified to use PyCrypto.
        """
        k = ['\0'] * 16
        k[0] = sn[-1]
        k[1] = '\0'
        k[2] = sn[-2]
        k[3] = 'T'
        k[4] = sn[-3]
        k[5] = '\x10'
        k[6] = sn[-4]
        k[7] = 'B'
        k[8] = sn[-1]
        k[9] = '\0'
        k[10] = sn[-2]
        k[11] = 'H'
        k[12] = sn[-3]
        k[13] = '\0'
        k[14] = sn[-4]
        k[15] = 'P'
        self.aes = AES.new(string.join(k, ''), AES.MODE_ECB)


    def subscribe(self, tgt):
        """
        Subscribe to the received packets.
        """
        self.subscribers.append(tgt)

    def unsubscribe(self, tgt):
        """
        Unsubscribe from the received packets.
        """
        self.subscribers.remove(tgt)


    def contact_resistance(self, contact):
        """
        Compute the contact resistance from the CQ value using an empirical
        4th order poly relationship.  Returns a number and a string indicating
        the contact resistance.  The resistance unit is kOhm.
        """
        cq = self.cq[contact]

        # return a very high value for CQ under 200 to indicate a BAD connection
        if cq < 260:
            return None, "No contact"

        # if the value if very high, indicate excellent quality
        if cq > 1026:
            return 4, "Excellent"

        cq = (cq - 673.5) / 315.6328        
        cr = -12.7629 * cq**4 - 31.3003 * cq**3 + 12.1686 * cq**2 - 0.4063 * cq + 51.5679

        return cr, "%.0f kOhm" % cr
