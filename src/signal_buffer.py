

#
# This implements a rolling signal buffer that always provides a coherent
# view of the current acquired EEG data.
#

import numpy as np

from emotiv_data_packet import EmotivDataPacket
from emotiv_device import EmotivDevice


class SignalBuffer:
    """
    The buffer in this class is twice as big as what has to be available
    at any time from the device.  Through a suitable write strategy, the
    buffer will always contain a contiguous segment of available EEG data.
    """


    def __init__(self, buf_len, sig_cnt):
        """
        Initialize the buffer, allocate memory.
        """
        self.buf = np.ones((buf_len * 2, sig_cnt), dtype = np.float) * 8000
        self.buf_len = buf_len
        self.sig_cnt = sig_cnt
        self.valid_region_start = 0
        self.valid_region_end = 0


    def buffer(self):
        """
        Access the region with data of len buf_len.  Part of the buffer
        may be filled with zeros if not enough data has been acquired yet.
        """
        start = self.valid_region_start
        return self.buf[start:start+self.buf_len, :]


    def pull_packets(self, dev):
        """
        Pull all available packets from the packet queue in the device and
        update the buffer.
        """
        # get handles to current state
        rend = self.valid_region_end
        buf = self.buf
        N = self.buf_len

        pulled = 0
        while not dev.packet_queue.empty():

            # extract packet from queue
            packet = dev.packet_queue.get()

            if rend < buf.shape[0] - 1:

                # store at current write position
                buf[rend, :] = packet.eeg

                # if write position is past roll point write to beginning
                # as well
                if rend > self.buf_len:
                    buf[rend - N, :] = packet.eeg

                # move write position
                rend += 1

            else:

                # we have passed the allocated memory end
                # double writing strategy ensures we have history at beginning
                # N - 1 values, now we write the last element
                rend = N - 1

                buf[rend, :] = packet.eeg
                rend += 1

            dev.packet_queue.task_done()
            pulled += 1

        # update the start position
        self.valid_region_end = rend
        self.valid_region_start = max(0, rend - N)

        return pulled


    def clear(self):
        """
        Used to clear the GUI from movements.
        """
        self.buf[:] = 0.0
