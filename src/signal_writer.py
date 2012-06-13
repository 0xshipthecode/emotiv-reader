

#
#  This class is responsible for sinking a signal to a file.  The signal
#  is stored as is (that is short samples) and written into a csv file.
#
#

import string


class SignalWriter:
    """
    Stores acquired signals packets in a CSV file.
    """


    def __init__(self):
        """
        Initialize the writer.
        """
        self.f = None
        self.fmt = '%d'


    def open(self, fname):
        self.fname = fname
        try:
            self.f = open(fname, 'w')
        except IOError as ioe:
            print(ioe)

    def close(self):
        self.f.close()
        self.f = None

    def ready(self):
        return self.f != None

    def write_packet(self, p):
        data = [p.counter, p.gyro_x, p.gyro_y]
        data.extend(p.eeg)
        data.append(p.cq_val if p.counter < 14 else -1)

        self.f.write(string.join([str(s) for s in data], ', '))
        self.f.write('\n')
            
