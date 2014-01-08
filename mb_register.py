#!/usr/bin/env python

import struct
import pp_functions

# key = data_type id, value = (size_in_bytes, pack string)
data_type_info = {'int16u': (2, ">H")}

class MBRegister:
    def __init__(self, address, name, data_type='int16u', pp_func='', pp_params=[]):
        # more types to be added later maybe!
        if not isinstance(address, int):
            raise TypeError('address must be an integer')
        if not isinstance(name, str):
            raise TypeError('name must be a string')
        if data_type not in data_type_info.keys():
            raise ValueError('data_type not known: %s' % data_type)
        pp_functions.check(pp_func, *pp_params)

        self.address = address
        self.name = name
        self.data_type = data_type
        self.pp_func = pp_func
        self.pp_params = pp_params
        self.size = data_type_info[data_type][0]
        self.pack = data_type_info[data_type][1]
        self.raw_value = None
        self.pp_value = None

    def __repr__(self):
        return "MBRegister(address=%d, name='%s', data_type='%s', pp_func='%s', pp_params=%s" % (
            self.address, self.name, self.data_type, self.pp_func, repr(self.pp_params) )

    def read(self, data):
        """ data is a bytearray which will be converted to raw data """
        self.raw_value = struct.unpack(self.pack, data)[0]
        self.pp_value = None

    def set(self, value):
        """ value is the raw value to be set.  This is probably a useless function which
            will never be used except in testing """
        self.raw_value = value
        self.pp_value = None

    def get(self, raw=True):
        """ get the value - if raw =# True return the raw value, else 
            return the post-processed value
        """
        if raw or self.pp_func == '':
            return self.raw_value
        else:
            if self.pp_value is None and self.raw_value is not None:
                self.pp_value = pp_functions.post_process(self.pp_func, self.raw_value, *self.pp_params)
            return self.pp_value

if __name__ == '__main__':
    def c_to_k(c):
        return c - 274.15

    def linear_scale(c, s):
        return c * s

    pp_functions.register(c_to_k)
    pp_functions.register(linear_scale)

    r1 = MBRegister(1, 'Volts')
    print repr(r1)
    r2 = MBRegister(address=2, name='Temp', pp_func='c_to_k')
    print repr(r2)
    r3 = MBRegister(address=3, name='Amps', pp_func='linear_scale', pp_params=[3.1])
    print repr(r3)

    data = bytearray([0x00, 0x10])
    print "r1.read(%s)" % repr(data)
    r1.read(data)
    print "r1 raw value = %d" % r1.get(raw=True)
    print "r1 pp value  = %s" % r1.get(raw=False)

    print "r2.read(%s)" % repr(data)
    r2.read(data)
    print "r2 raw value = %d" % r2.get(raw=True)
    print "r2 pp value  = %s" % r2.get(raw=False)

    print "r3.read(%s)" % repr(data)
    r3.read(data)
    print "r3 raw value = %d" % r3.get(raw=True)
    print "r3 pp value  = %s" % r3.get(raw=False)



