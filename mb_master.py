#!/usr/bin/env python

import ConfigParser
import serial
from mb_register import MBRegister
from mb_slave import MBSlave

class MBMaster:
    def __init__(self, config_file="/etc/phealth.conf"):
        self.slaves = dict()
        # defaults for master configuration
        self.config_file = config_file
        self.read_config_file()

    def read_config_file(self):
        parser = ConfigParser.SafeConfigParser( {
            'serial_device':     '/dev/ttyUSB0',
            'serial_baud':       '115200',
            'serial_bytesize':   '8',
            'serial_parity':     'none',
            'serial_stopbits':   '2',
            'serial_timeout':    '0.015',
            'raw_mode':          'false',
            'poll_time':         '0.5',
        } )
        parser.read(self.config_file)
        self.serial_device = parser.get('master','serial_device')
        self.serial_baud = parser.getint('master','serial_baud')
        self.serial_bytesize = parser.getint('master','serial_bytesize')
        self.serial_parity = parser.get('master','serial_parity',{'none':serial.PARITY_NONE, 'odd':serial.PARITY_ODD, 'even': serial.PARITY_EVEN, 'mark': serial.PARITY_MARK})
        self.serial_stopbits = parser.getint('master','serial_stopbits')
        self.serial_timeout = parser.getfloat('master','serial_timeout')
        self.poll_time = parser.getfloat('master','poll_time')

        # Now read slave sections
        for sec in [s for s in parser.sections() if s[:6] == 'slave_']:
            try:
                address = int(sec[6:])
                if 'name' in [s[0] for s in parser.items(sec)]:
                    name = parser.get(sec,'name')
                else:
                    name = sec
                print "address=%s, name=%s" % (repr(address), repr(name))
                slave = MBSlave(address = address, name = name)
                self.add_slave(slave)
            except Exception as e:
                print "ERROR: failed add slave for section '%s' because %s/%s" % (sec, type(e), e)


        print repr(self)
        print self.repr_config()
        print 'slaves:'
        for s in self.slaves:
            print '+ %s' % repr(self.slaves[s])

    def __repr__(self):
        return "MBMaster(config_file='%s')" % self.config_file

    def repr_config(self):
        return "serial_device=%s, serial_baud=%s, serial_bytesize=%s, serial_parity=%s, serial_stopbits=%s, serial_timeout=%s, poll_time=%s" % (
                repr(self.serial_device),
                repr(self.serial_baud),
                repr(self.serial_bytesize),
                repr(self.serial_parity),
                repr(self.serial_stopbits),
                repr(self.serial_timeout),
                repr(self.poll_time) )

    def add_slave(self, slave):
        if not isinstance(slave, MBSlave):
            raise TypeError('must be MBSlave')
        self.slaves[slave.address] = slave

if __name__ == '__main__':
    m = MBMaster('./phealth.conf')
   
