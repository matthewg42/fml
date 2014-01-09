#!/usr/bin/env python

import ConfigParser
import serial
import re
import time
from mb_register import MBRegister
from mb_slave import MBSlave
from pretty_format import PrettyFormat, PfFloat, PfInt

class MBMaster:
    def __init__(self, config_file="/etc/fml.conf"):
        self.slaves = dict()
        # defaults for master configuration
        self.config_file = config_file
        self.times = None
        self.read_config_file()

    def read_config_file(self):
        parser = ConfigParser.SafeConfigParser( {
            'serial_device':    '/dev/ttyUSB0',
            'serial_baud':      '115200',
            'serial_bytesize':  '8',
            'serial_parity':    'none',
            'serial_stopbits':  '2',
            'serial_timeout':   '0.015',
            'raw_mode':         'false',
            'interval':         '0.5',
        } )
        parser.read(self.config_file)
        self.serial_device = parser.get('master','serial_device')
        self.serial_baud = parser.getint('master','serial_baud')
        self.serial_bytesize = parser.getint('master','serial_bytesize')
        self.serial_parity = parser.get('master','serial_parity',{'none':serial.PARITY_NONE, 'odd':serial.PARITY_ODD, 'even': serial.PARITY_EVEN, 'mark': serial.PARITY_MARK})
        self.serial_stopbits = parser.getint('master','serial_stopbits')
        self.serial_timeout = parser.getfloat('master','serial_timeout')
        self.interval = parser.getfloat('master','interval')

        # Now read slave sections
        for sec in [s for s in parser.sections() if s[:6] == 'slave_']:
            try:
                address = int(sec[6:])
                if 'name' in [s[0] for s in parser.items(sec)]:
                    name = parser.get(sec,'name')
                else:
                    name = sec
                slave = MBSlave(address = address, name = name)

                # extract register details
                rexp = re.compile('^r(\d+)_name$')
                for item in [i for i in parser.items(sec) if rexp.match(i[0]) is not None]:
                    addr_str = rexp.match(item[0]).groups()[0]
                    address = int(addr_str)
                    name = item[1]
                    pp_func = ''
                    pp_params = []
                    raw_type = 'uint16'
                    pp_type = 'float'
                    if 'r%s_pp_fn'%addr_str in [s[0] for s in parser.items(sec)]:
                        pp_func = parser.get(sec, 'r%s_pp_fn'%addr_str)
                    if 'r%s_pp_param'%addr_str in [s[0] for s in parser.items(sec)]:
                        pp_params = parser.get(sec, 'r%s_pp_param'%addr_str).split(',')
                    if 'r%s_raw_type'%addr_str in [s[0] for s in parser.items(sec)]:
                        raw_type = parser.get(sec, 'r%s_raw_type'%addr_str)
                    if 'r%s_pp_type'%addr_str in [s[0] for s in parser.items(sec)]:
                        pp_type = parser.get(sec, 'r%s_pp_type'%addr_str)
                    pf = {'float': PfFloat, 'int': PfInt}[pp_type]
                    #print "addr_str=%s, address=%s, name=%s, pp_func=%s, pp_params=%s, raw_type=%s, pp_type=%s, pf=%s" % (
                    #    repr(addr_str),
                    #    repr(address),
                    #    repr(name),
                    #    repr(pp_func),
                    #    repr(pp_params),
                    #    repr(raw_type),
                    #    repr(pp_type),
                    #    repr(pf) )
                    slave.add_register(MBRegister(address=address, name=name, mb_type=raw_type, pp_func=pp_func, pp_params=pp_params, pp_type=pp_type, pf=pf))
                self.add_slave(slave)
            except Exception as e:
                print "ERROR: failed add slave for section '%s' because %s/%s" % (sec, type(e), e)
                raise

    def __repr__(self):
        return "MBMaster(config_file='%s')" % self.config_file

    def repr_config(self):
        s = "serial_device=%s, serial_baud=%s, serial_bytesize=%s, serial_parity=%s, serial_stopbits=%s, serial_timeout=%s, interval=%s" % (
                repr(self.serial_device),
                repr(self.serial_baud),
                repr(self.serial_bytesize),
                repr(self.serial_parity),
                repr(self.serial_stopbits),
                repr(self.serial_timeout),
                repr(self.interval) )
        s = s + "\nSlaves:"
        for sl in self.slaves.keys():
            s = s + '\n+ %s' % repr(self.slaves[sl])
        return s

    def add_slave(self, slave):
        if not isinstance(slave, MBSlave):
            raise TypeError('must be MBSlave')
        self.slaves[slave.address] = slave

    def run(self):
        while True:
            loop_start_time = time.time()
            
            print "fetching..."

            # If we are only running some fixed number of times, check 
            # if we're done and break out of look if so.
            if self.times is not None:
                self.times -= 1
                if self.times == 0:
                    break

            # Decide how long to wait until the delay between fetches is
            # done.  Warn if we've gone over it.
            wait_time = loop_start_time + self.wait - time.time()
            if wait_time > 0:
                time.sleep(wait_time)
            #else:
            #    self.log.warning

if __name__ == '__main__':
    m = MBMaster('./fml.conf')
    print repr(m)
    print m.repr_config()
