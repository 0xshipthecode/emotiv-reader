
import time

from emotiv_device import EmotivDevice
from emotiv_data_packet import EmotivDataPacket
from signal_buffer import SignalBuffer



if __name__ == '__main__':
    
    print("Setting up device ...")

    dev = EmotivDevice('SN20120229000254')
    
    print("Starting reader ...")

    dev.start_reader()

    rb = SignalBuffer(64, 14)
    
    for rbp in range(10):
        pp = rb.pull_packets(dev)
        print("Pulled %d packets." % pp)
        print rb.buffer().shape
        time.sleep(0.2)

    print("Stopping reader ...")

    dev.stop_reader()

    print("Done.")
