
import time

from emotiv_device_monitor import EmotivDeviceMonitor
from emotiv_device import EmotivDevice

def print_event(connected):
    print(connected)


dev = EmotivDevice('SN20120229000254')
mon = EmotivDeviceMonitor()
mon.callbacks.append(print_event)

mon.start()

time.sleep(10.0)

mon.stop()
