#!/usr/bin/env python

import ConfigParser
import serial
import re
import time
import logging
from mb_register import MBRegister
from mb_slave import MBSlave
from pretty_format import PrettyFormat, PfFloat, PfInt

global log
log = None

class MBMaster:
    def __init__(self, config_file="/etc/fml.conf", cl_args={}):
        self.slaves = dict()
        # defaults for master configuration
        self.config_file = config_file
        self.times = None
        self.output_file = None
        self.output_format = None
        self.daemon = False
        self.read_config_file(cl_args)

    def read_config_file(self, cl_args={}):
        if log: log.debug('MBMaster reading config from %s' % repr(self.config_file))
        p = ConfigParser.SafeConfigParser( {
            'serial_device':    '/dev/ttyUSB0',
            'serial_baud':      '115200',
            'serial_bytesize':  '8',
            'serial_parity':    'none',
            'serial_stopbits':  '2',
            'serial_timeout':   '0.015',
            'raw_mode':         'false',
            'interval':         '0.5',
            'output_format':    'pretty',
            'output_file':      None
        } )
        p.read(self.config_file)
        self.serial_device   = cl_args['serial_device']   if 'serial_device'   in cl_args else p.get('master','serial_device')
        self.serial_baud     = cl_args['serial_baud']     if 'serial_baud'     in cl_args else p.getint('master','serial_baud')
        self.serial_bytesize = cl_args['serial_bytesize'] if 'serial_bytesize' in cl_args else p.getint('master','serial_bytesize')
        self.serial_parity   = cl_args['serial_parity']   if 'serial_parity'   in cl_args else p.get('master','serial_parity')
        self.serial_parity = {  'none':serial.PARITY_NONE, 
                                'odd':serial.PARITY_ODD, 
                                'even': serial.PARITY_EVEN, 
                                'mark': serial.PARITY_MARK }[self.serial_parity]
        self.serial_stopbits = cl_args['serial_stopbits'] if 'serial_stopbits' in cl_args else p.getint('master','serial_stopbits')
        self.serial_timeout  = cl_args['serial_timeout']  if 'serial_timeout'  in cl_args else p.getfloat('master','serial_timeout')
        self.interval        = cl_args['interval']        if 'interval'        in cl_args else p.getfloat('master','interval')
        self.raw_mode        = cl_args['raw_mode']        if 'raw_mode'        in cl_args else p.getboolean('master','raw_mode')
        self.output_format   = cl_args['output_format']   if 'output_format'   in cl_args else p.get('master','output_format')
        self.output_file     = cl_args['output_file']     if 'output_file'     in cl_args else p.get('master','output_file', True)

        # some args do not come from the config file - only from command line args, so we'll set them here if they exist
        if 'times' in cl_args: self.times = cl_args['times'] 
        if 'daemon' in cl_args: self.daemon = cl_args['daemon'] 

        # Now read slave sections
        for sec in [s for s in p.sections() if s[:6] == 'slave_']:
            try:
                address = int(sec[6:])
                if 'name' in [s[0] for s in p.items(sec)]:
                    name = p.get(sec,'name')
                else:
                    name = sec
                slave = MBSlave(address = address, name = name)

                # extract register details
                rexp = re.compile('^r(\d+)_name$')
                for item in [i for i in p.items(sec) if rexp.match(i[0]) is not None]:
                    addr_str = rexp.match(item[0]).groups()[0]
                    address = int(addr_str)
                    name = item[1]
                    pp_func = ''
                    pp_params = []
                    raw_type = 'uint16'
                    pp_type = 'float'
                    if 'r%s_pp_fn'%addr_str in [s[0] for s in p.items(sec)]:
                        pp_func = p.get(sec, 'r%s_pp_fn'%addr_str)
                    if 'r%s_pp_param'%addr_str in [s[0] for s in p.items(sec)]:
                        pp_params = p.get(sec, 'r%s_pp_param'%addr_str).split(',')
                    if 'r%s_raw_type'%addr_str in [s[0] for s in p.items(sec)]:
                        raw_type = p.get(sec, 'r%s_raw_type'%addr_str)
                    if 'r%s_pp_type'%addr_str in [s[0] for s in p.items(sec)]:
                        pp_type = p.get(sec, 'r%s_pp_type'%addr_str)
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

        if log:
            s = "MBMaster loaded configuration:\n%s\n%s" % (repr(self), self.dump_config())
            for line in s.split('\n'):
                log.info(line)

    def __repr__(self):
        return "MBMaster(config_file='%s')" % self.config_file

    def dump_config(self):
        s = "serial_device=%s, serial_baud=%s, serial_bytesize=%s, serial_parity=%s, serial_stopbits=%s, serial_timeout=%s" % (
                repr(self.serial_device),
                repr(self.serial_baud),
                repr(self.serial_bytesize),
                repr(self.serial_parity),
                repr(self.serial_stopbits),
                repr(self.serial_timeout))
        s += "\ndaemon=%s, times=%s, interval=%s, raw_mode=%s, output_file=%s, output_format=%s" % (
                repr(self.daemon),
                repr(self.times),
                repr(self.interval),
                repr(self.raw_mode),
                repr(self.output_file),
                repr(self.output_format) )
        s += "\nSlaves:"
        for sl in self.slaves.keys():
            s += '\n+ %s' % repr(self.slaves[sl]).replace('\n', '\n - ')
        return s

    def add_slave(self, slave):
        if not isinstance(slave, MBSlave):
            raise TypeError('must be MBSlave')
        self.slaves[slave.address] = slave

    def run(self):  
        num_warnings = 0
        num_errors = 0
        while True:
            loop_start_time = time.time()
            if log: log.debug('fetching from slaves...')

            for address, slave in self.slaves.items():
                if log: log.debug('fetching slave address=%d, name=%s' % (slave.address, slave.name))
                time.sleep(0.01)
            # If we are only running some fixed number of times, check 
            # if we're done and break out of look if so.
            if self.times is not None:
                self.times -= 1
                if self.times == 0:
                    break
            # Decide how long to wait until the delay between fetches is
            # done.  Warn if we've gone over it.
            fetch_time = time.time() - loop_start_time
            wait_time = self.interval - fetch_time
            if wait_time > 0:
                if log: log.debug('fetching slaves took %.3f secs, waiting for %.3f for interval' % (fetch_time, wait_time))
                time.sleep(wait_time)
            else:
                if log: log.warning('fetching slaves took %.3f sec, interval=%.3f. Consider raising interval.' % ( fetch_time, self.interval ))
                num_warnings += 1
        if log: log.debug('all iterations complete, exiting.')

if __name__ == '__main__':
    m = MBMaster('./fml.conf')
    print repr(m)
    print m.dump_config()

