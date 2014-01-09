#!/usr/bin/env python

import logging
import mb_crc
from struct import pack, unpack
from mb_register import MBRegister

global log
log = None

class MBSlave:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.registers = dict()
        self.last_fetched = None
        self.mb_query = None

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

    def update_mb_query(self):
        # should be called after registers have been added
        first=min(self.registers)
        count=max(self.registers)-first+1
        query = bytearray(pack("B", self.address))      # first the target slave address
        query.extend(bytearray(pack("B", 3)))           # then the operation (3 = fetch holding regs)
        query.extend(bytearray(pack(">H", first)))      # then the first register to fetch as a 2 byte int
        query.extend(bytearray(pack(">H", count)))      # and the register count as a 2 byte int
        query.extend(mb_crc.calculate_crc(query))       # finally calculate and append the checksum
        if log: log.debug('build_query register=%d, first=%d, count=%d -> query: %s' % (self.address, first, count, repr(query)))
        self.mb_query = query

    def clear_regs(self):
        for r_add, register in self.registers.items():
            register.clear()

    def set_values(self, reply):
        # decode the reply
        if log: log.debug('decoding the reply %s' % repr(reply))
        if len(reply) < 7:
            raise Exception("invalid reply: too short")
        # check CRC
        crc = mb_crc.calculate_crc( bytearray( reply[:-2] ) )
        if bytearray(reply[-2:]) != crc:
            raise Exception("invalid reply: bad checksum")
        # remove non-data items
        num_bytes = ord(reply[2])
        if len(reply) != num_bytes + 5: # address (1 byte) function (1 byte), num_bytes (1 byte), crc (2 bytes)
            raise Exception('invalid reply: %d bytes means %d reply size, but got %d' % (num_bytes, num_bytes+5, len(reply)))
        # strip non-payload
        reply = reply[3:][:-2] # strip reply so it's just data
        
        # extract those values...
        for r_add, register in self.registers.items():
            register.read(reply[:register.size])
            reply = reply[register.size:]  # pop from the front of the reply...
            # if log: log.debug('reply now: %s' % repr(reply))

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
    s.update_mb_query()

    print repr(s)
    print "query is: %s" % repr(s.mb_query)


