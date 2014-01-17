#!/usr/bin/env python

import struct
import pp_functions
import logging
from pretty_format import PrettyFormat, PfFloat, PfInt
import re

global log
log = None

# key = mb_type id, value = (size_in_bytes, pack string, default format)
mb_type_info = {'uint16': (2, '>H', PfInt()),
                'float': (4, 'f', PfFloat())}
pp_type_info = {'float': float, 'int': int}

class MBRegister:
    def __init__(self, address, name, mb_type='uint16', pp_func='', pp_params=[], pp_type='float', pf=None, display=True):
        # more types to be added later maybe!
        if not isinstance(address, int):
            raise TypeError('address must be an integer')
        if not isinstance(name, str):
            raise TypeError('name must be a string')
        if mb_type not in mb_type_info.keys():
            raise ValueError('mb_type not known: %s' % mb_type)
        if pp_type not in pp_type_info.keys():
            raise TypeError('pp_type not known: %s')
        if pf is not None and not isinstance(pf, PrettyFormat):
            raise TypeError('pf must be a PrettyFormat object')
        pp_functions.check(pp_func, *pp_params)

        self.address = address
        self.name = name
        self.mb_type = mb_type
        self.pp_func = pp_func
        self.pp_params = pp_params
        self.display = display
        self.size = mb_type_info[mb_type][0]
        self.pack = mb_type_info[mb_type][1]
        if pf == None:
            self.pf = PrettyFormat()
        else:
            self.pf = pf
        self.pf.expand_to_fit(self.name)
        self.raw_value = None
        self.pp_value = None

    def __repr__(self):
        return "MBRegister(address=%d, name='%s', mb_type='%s', pp_func='%s', pp_params=%s, pf=%s, display=%s)" % (
            self.address, self.name, self.mb_type, self.pp_func, repr(self.pp_params), repr(self.pf), repr(self.display) )

    def clear(self):
        self.raw_value = None
        self.pp_value = None

    def set(self, value):
        """ value is the raw value to be set.  This is probably a useless function which
            will never be used except in testing """
        self.raw_value = value
        self.pp_value = None

    def get(self, raw=False):
        """ get the value - if raw = True return the raw value, else 
            return the post-processed value
        """
        if raw or self.pp_func == '':
            return self.raw_value
        else:
            if self.pp_value is None and self.raw_value is not None:
                try:
                    self.pp_value = pp_functions.post_process(self.pp_func, self.raw_value, *self.pp_params)
                except ValueError as e:
                    if log: log.debug('ValueError when calling post_processing function %s : %s' % (self.pp_func, e))
                    self.pp_value = None
                    pass
                except Exception as e:
                    if log: log.debug('Exception when calling post_processing function %s : %s' % (self.pp_func, e))
                    self.pp_value = None
                    pass
            return self.pp_value

    def read(self, data):
        """ data is a bytearray which will be converted to raw data """
        self.set(struct.unpack(self.pack, data)[0])

    def pretty_header(self):
        return self.pf.fmtstr(string=True) % self.name

    def pretty_value(self, raw=False):
        v = self.get(raw)
        r = self.pf.out(v)
        return r

if __name__ == '__main__':
    from pretty_format import PrettyFormat, PfInt, PfFloat, PfTimestamp
    import datetime
    import random
    def c_to_k(c):
        return c - 274.15

    def linear_scale(c, s):
        return c * s

    pp_functions.register(c_to_k)
    pp_functions.register(linear_scale)

    data = bytearray([0x00, 0x10])
    regs = [MBRegister(1, 'Volts', pf=PfInt), 
            MBRegister(address=2, name='Temp', pp_func='c_to_k', pf=PfFloat),
            MBRegister(address=3, name='Amps', pp_func='linear_scale', pf=PfFloat, pp_params=[3.1])]

    for r in regs:
        print repr(r)
        print "r.read(%s)" % repr(data)
        r.read(data)
        print "r raw value = %d" % r.get(raw=True)
        print "r pp value  = %s" % r.get(raw=False)
        print "r pretty header = '%s'" % r.pretty_header()
        print "r underline =     '%s'" % r.pf.underline()
        print "r pretty value  = '%s'" % r.pretty_value()
        print ""

    # fun time
    print " | ".join([r.pf.underline() for r in regs])
    print " | ".join([r.pretty_header() for r in regs])
    print " | ".join([r.pf.underline() for r in regs])
    for n in range(0,300, 14):
        for r in regs:
            #r.set(n)
            r.set(random.random()*30)
        print " | ".join([r.pretty_value() for r in regs])
    print " | ".join([r.pf.underline() for r in regs])
        


