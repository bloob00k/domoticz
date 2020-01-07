import struct

BLUEMAESTRO_MFR_CODE = 0x0133


class tempo_data:
    
    def __init__(self, data, data1=None):
        version = struct.unpack('=B', data[0:1])[0]
        if version != 13 and version != 0:
            raise ValueError('Unsupported tempo advertisement data format version', version)

        if version == 0:
            (self.temp_high,
             self.humidity_high,
             self.temp_low, 
             self.humidity_low,
             self.temp_24high,
             self.humidity_24_high,
             self.temp_24_low,
             self.humidity_24_low) = struct.unpack('>HHHHHHHH', data[1:17])
        elif data1:
            (self.temp_high,
             self.humidity_high,
             self.temp_low, 
             self.humidity_low,
             self.temp_24high,
             self.humidity_24_high,
             self.temp_24_low,
             self.humidity_24_low) = struct.unpack('>HHHHHHHH', data1[:16])
        else:
            self.temp_high = None
            self.humidity_high = None
            self.temp_low = None 
            self.humidity_low = None
            self.temp_24high = None
            self.humidity_24_high = None
            self.temp_24_low = None
            self.humidity_24_low = None

        if version == 13:
            (self.battery,
             self.time_interval,
             self.stored_logcount,
             self.temp,
             self.humidity,
             self.dewpoint,
             self.mode,
             self.breach_count) = struct.unpack('>BHHHHHBB', data[1:])

            self.temp /= 10.0
            self.humidity /= 10
        else:
            self.battery = None
            self.time_interval = None
            self.stored_logcount = None
            self.temp = None
            self.humidity = None
            self.dewpoint = None
            self.mode = None
            self.breach_count  = None

            
