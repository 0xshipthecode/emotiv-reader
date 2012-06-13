
import numpy as np


#
# EmotivDataPacket is a class based on information from emotiv.py of the Emokit
# project.  
#


# This data structure is copied verbatim from the emotiv.py file
sensor_bits = {
  'F3': [10, 11, 12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7], 
  'FC6': [214, 215, 200, 201, 202, 203, 204, 205, 206, 207, 192, 193, 194, 195], 
  'P7': [84, 85, 86, 87, 72, 73, 74, 75, 76, 77, 78, 79, 64, 65], 
  'T8': [160, 161, 162, 163, 164, 165, 166, 167, 152, 153, 154, 155, 156, 157], 
  'F7': [48, 49, 50, 51, 52, 53, 54, 55, 40, 41, 42, 43, 44, 45], 
  'F8': [178, 179, 180, 181, 182, 183, 168, 169, 170, 171, 172, 173, 174, 175], 
  'T7': [66, 67, 68, 69, 70, 71, 56, 57, 58, 59, 60, 61, 62, 63], 
  'P8': [158, 159, 144, 145, 146, 147, 148, 149, 150, 151, 136, 137, 138, 139], 
  'AF4': [196, 197, 198, 199, 184, 185, 186, 187, 188, 189, 190, 191, 176, 177], 
  'F4': [216, 217, 218, 219, 220, 221, 222, 223, 208, 209, 210, 211, 212, 213], 
  'AF3': [46, 47, 32, 33, 34, 35, 36, 37, 38, 39, 24, 25, 26, 27], 
  'O2': [140, 141, 142, 143, 128, 129, 130, 131, 132, 133, 134, 135, 120, 121], 
  'O1': [102, 103, 88, 89, 90, 91, 92, 93, 94, 95, 80, 81, 82, 83], 
  'FC5': [28, 29, 30, 31, 16, 17, 18, 19, 20, 21, 22, 23, 8, 9],
  'CQ' : [119, 104, 105, 106, 107, 108, 109, 110, 111, 96, 97, 98, 99, 100]
}


# The position of the sensor ID in the numpy array
sensor_id_to_ndx = { 'F3' : 0, 'FC5' : 1, 'AF3' : 2, 'F7' : 3, 'T7' : 4, 'P7' : 5,
                     'O1' : 6, 'O2' : 7, 'P8' : 8, 'T8' : 9, 'F8' : 10, 'AF4' : 11,
                     'FC6' : 12, 'F4' : 13 }

counter_to_sensor_id = [ 'F3', 'FC5', 'AF3', 'F7', 'T7', 'P7', 'O1', 'O2',
                         'P8', 'T8', 'F8', 'AF4', 'FC6', 'F4' ]



class EmotivDataPacket:
    """
    The EEG signals are stored as floats in the data packet in anticipation
    of further processing.  The data packet contains:
      - EEG signal levels (128Hz)
      - EEG contact quality once per second (TODO)
      - Gyro positions X,Y (128Hz)
      - Battery levels (once per second)
    """

    def __init__(self, raw_data):
        """
        Initialize the packet with raw data read in from the device.
        """

        # packet counter is first byte [0..127]
        counter = ord(raw_data[0])

        # if counter > 127, then it's the battery status
        # and the packet number is 128
        if counter > 127:
            self.battery = max(min(1.0, (float(counter) - 225.0) / (248.0 - 225.0)), 0.0)
            self.counter = 128
        else:
            self.battery = None
            self.counter = counter

        # what's this?
        self.sync = (self.counter == 0xe9)

        # decode gyro positions
        self.gyro_x = ord(raw_data[29])
        self.gyro_y = ord(raw_data[30])

        # allocate numpy array for eeg samples & decode data into it
        # each electrode is a 14-bit value (??)
        self.eeg = np.zeros((14,), dtype = np.float)
        for i in range(14):
          self.eeg[i] = self.get_bits_from_raw(raw_data, sensor_bits[counter_to_sensor_id[i]])
          
        # read out the CQ for packets 0 to 13
        if self.counter < 14:
            self.cq_id = counter_to_sensor_id[self.counter]
            self.cq_val = self.get_bits_from_raw(raw_data, sensor_bits['CQ'])
#            self.cq_val = None
        else:
            self.cq_id = None
            self.cq_val = None

        
    def __getattr__(self, attr):
        """
        Return the sample for the requested channel id.
        """
        return self.eeg[sensor_id_to_ndx[attr]]


    def get_bits_from_raw(self, raw_data, bit_list):
        """
        Routine copied practically verbatim from emotiv.py, probably does not
        need to be more effective/faster.  Returns the 14-bit level of the
        signal (baseline seems to be 2**12).
        """
        level = 0
        for i in range(13, -1, -1):
            level <<= 1
            b, o = divmod(bit_list[i], 8)
            level |= (ord(raw_data[b+1]) >> o) & 1
        return float(level)
