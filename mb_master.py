#!/usr/bin/env python

import ConfigParser
import serial
import re
import os
import sys
import time
import datetime
import logging
from mb_register import MBRegister
from mb_slave import MBSlave
from pretty_format import PrettyFormat, PfFloat, PfInt

# TODO: remove this once we don't need test data
import random

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
        self.stats = {'iterations': 0, 'warnings': 0, 'errors': 0}
        self.read_config_file(cl_args)
        self.output_fd = None
        self.serial = None

    def read_config_file(self, cl_args={}):
        if log: log.debug('MBMaster reading config from %s' % repr(self.config_file))

        # some args do not come from the config file - only from command line args, so we'll set them here if they exist
        if 'times' in cl_args: self.times = cl_args['times'] 
        if 'daemon' in cl_args: self.daemon = cl_args['daemon'] 

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
        if self.daemon:
            self.output_file     = cl_args['output_file']     if 'output_file'     in cl_args else p.get('master','output_file', True)
        else:
            self.output_file = cl_args['output_file'] if 'output_file' in cl_args else None


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
        self.open_serial_port()
        self.open_output_file()
        self.output_headers()

        while True:
            loop_start_time = time.time()
            if log: log.debug('fetching from slaves...')

            self.query_slaves()
            self.output_data((loop_start_time + time.time()) / 2)  # average now and loop start to give most "middle" time... :s

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
                self.stats['warnings'] += 1
            self.stats['iterations'] += 1
        if log: log.debug('all iterations complete, exiting.')

    def open_serial_port(self):
        self.serial = serial.Serial(port=self.serial_device, 
                                    baudrate=self.serial_baud, 
                                    parity=self.serial_parity, 
                                    stopbits=self.serial_stopbits, 
                                    bytesize=self.serial_bytesize, 
                                    timeout=self.serial_timeout)
        # add a short delay for the serial device to "warm up"
        # if this is not done, the first traffic may get corrupted
        time.sleep(0.15)

    def open_output_file(self):
        if self.output_file is None or self.output_file == '-':
            self.output_fd = sys.stdout
        else:
            self.output_file = datetime.datetime.now().strftime(self.output_file)
            if log: log.info('output file is: %s' % self.output_file)
            if os.path.exists(self.output_file):
                raise Exception("output file already exists: %s" % self.output_file)
            self.output_fd = open(self.output_file, 'w')

    def output_headers(self):
        if self.output_format == 'csv':
            self.output_headers_csv()
        elif self.output_format == 'gnostic':
            self.output_headers_gnostic()
        elif self.output_format == 'pretty':
            self.output_headers_pretty()
        elif self.output_format == 'rrd':
            self.output_headers_rrd()
        else:
            raise ValueError('unknown output format %s' % repr(self.output_format))

    def query_slaves(self):
        for s_add, slave in self.slaves.items():
            if log: log.debug('fetching slave address=%d, name=%s  query=%s' % (s_add, slave.name, repr(slave.mb_query)))
            self.serial.write(slave.mb_query)
            # TODO: actually fetching registers
            for r_add, register in slave.registers.items():
                register.set(random.randint(700,1000))
            # simulate serial comms delay
            time.sleep(0.01)

    def output_data(self, timestamp):
        if self.output_format == 'csv':
            self.output_data_csv(timestamp)
        elif self.output_format == 'gnostic':
            self.output_data_gnostic(timestamp)
        elif self.output_format == 'pretty':
            self.output_data_pretty(timestamp)
        elif self.output_format == 'rrd':
            self.output_data_rrd(timestamp)
        else:
            raise ValueError('unknown output format %s' % repr(self.output_format))

    def output_headers_csv(self):
        a = ['timestamp']
        for s_add, slave in self.slaves.items():
            for r_add, register in slave.registers.items():
                if register.display:
                    a.append(register.name.replace(',','\\,'))
        self.output_fd.write(",".join(a) + "\n")

    def output_data_csv(self, timestamp):
        a = [datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %T.%f")[:-3]]
        for s_add, slave in self.slaves.items():
            for r_add, register in slave.registers.items():
                if register.display:
                    a.append(register.pretty_value().replace(' ',''))
        self.output_fd.write(",".join(a) + "\n")

if __name__ == '__main__':
    m = MBMaster('./fml.conf')
    print repr(m)
    print m.dump_config()

