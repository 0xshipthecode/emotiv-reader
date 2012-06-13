

import os
import stat
import time
import threading


class EmotivDeviceMonitor:
    """
    Monitors the /dev/eeg/encrypted device to check for devic insertion/removal.
    Notifies all callbacks of the device appearing/dissapearing.
    """

    def __init__(self, dev_name = '/dev/eeg/encrypted', callback_list = []):
        self.dev_name = dev_name
        self.stop_monitoring = False
        self.callbacks = callback_list or []
        self.current_state = False
        self.monitor = None


    def start(self):
        """
        Start the monitoring thread.
        """
        if self.monitor is None:
            self.monitor = threading.Thread(target = self.monitor_func)
            self.monitor.start()


    def check_connected(self):
        """
        Check if the device is connected.
        Update the status accordingly.
        """
        new_state = os.path.exists(self.dev_name)
        if new_state != self.current_state:
            #state changed, update everybody
            for cb in self.callbacks:
                cb(new_state)

        self.current_state = new_state
        return self.current_state


    def monitor_func(self):
        """
        Monitors the device file for appearance/dissapearance and updates the GUI
        and Emotiv Device status.
        """
        self.stop_monitoring = False

        while not self.stop_monitoring:
            self.check_connected()
            time.sleep(0.1)


    def stop(self):
        """
        Stop the monitoring thread.
        """
        self.stop_monitoring = True
        self.monitor.join()
        self.monitor = None
