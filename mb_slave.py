#!/usr/bin/env python

from mb_register import MBRegister

class MBSlave:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.registers = dict()
        self.last_fetched = None

    def __repr__(self):
        s = 'MBSlave address=%d, name="%s", has %d registers:\n - ' % ( self.address, self.name, len(self.registers) )
        s = s + "\n - ".join([repr(self.registers[a]) for a in sorted(self.registers.keys())])
        return s

    def add_register(self, register):
        if not isinstance(register, MBRegister):
            raise TypeError('must be MBRegister')
        self.registers[register.address] = register
        
if __name__ == '__main__':
    import pp_functions
    def c_to_k(c):
        return c - 274.15

    def linear_scale(c, s):
        return c * s

    pp_functions.register(c_to_k)
    pp_functions.register(linear_scale)

    # Demo/test
    s = MBSlave(1, 'Tom Waits')
    s.add_register(MBRegister(address=1, name='Temp', pp_func='c_to_k'))
    s.add_register(MBRegister(address=2, name='Volts', pp_func='linear_scale', pp_params=[6.666]))
    s.add_register(MBRegister(address=3, name='Current'))

    print repr(s)


