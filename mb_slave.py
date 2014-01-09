#!/usr/bin/env python

import logging
import mb_crc
from struct import pack
from mb_register import MBRegister

global log
log = None

class MBSlave:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.registers = dict()
        self.last_fetched = None

    def __repr__(self):
        s = 'MBSlave address=%d, name="%s", has %d register%s%s' % ( 
            self.address, 
            self.name, len(self.registers), 
            ('s' if len(self.registers) != 1 else '') ,
            (':' if len(self.registers) > 0 else '') )
        for r in [repr(self.registers[r]) for r in self.registers]:
            s = s + "\n%s" % r
        return s

    def add_register(self, register):
        if not isinstance(register, MBRegister):
            raise TypeError('must be MBRegister')
        self.registers[register.address] = register
        # work out the modbus command (changes each time a register is added)
        first=min(self.registers)
        count=max(self.registers)-first+1
        query = bytearray(pack("B", self.address))      # first the target slave address
        query.extend(bytearray(pack("B", 3)))           # then the operation (3 = fetch holding regs)
        query.extend(bytearray(pack(">H", first)))      # then the first register to fetch as a 2 byte int
        query.extend(bytearray(pack(">H", count)))      # and the register count as a 2 byte int
        query.extend(mb_crc.calculate_crc(query))       # finally calculate and append the checksum
        if log: log.debug('build_query register=%d, first=%d, count=%d -> query: %s' % (self.address, first, count, repr(query)))
        self.mb_query = query

if __name__ == '__main__':
    import pp_functions
    def c_to_k(c):
        return c - 274.15

    def linear_scale(c, s):
        return c * s

    pp_functions.register(c_to_k)
    pp_functions.register(linear_scale)

    # Demo/test
    s = MBSlave(address=1, name='Tom Waits')
    s.add_register(MBRegister(address=0, name='Temp', pp_func='c_to_k'))
    s.add_register(MBRegister(address=2, name='Volts', pp_func='linear_scale', pp_params=[6.666]))
    s.add_register(MBRegister(address=11, name='Current'))

    print repr(s)
    print "query is: %s" % repr(s.mb_query)


