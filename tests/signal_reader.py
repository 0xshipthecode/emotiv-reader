

from emotiv_device import EmotivDevice
from emotiv_data_packet import EmotivDataPacket


if __name__ == '__main__':
    
    print("Setting up device ...")

    dev = EmotivDevice('SN20120229000254')
    
    print("Starting reader ...")

    dev.start_reader()

    for pc in range(1000):
        p = dev.packet_queue.get()
        print("%d: gyroX: %d  gyroY: %d F3 : %g F4: %g" % (p.counter, p.gyro_x, p.gyro_y, p.F3, p.F4))

    print("Stopping reader ...")

    dev.stop_reader()

    print("Done.")
