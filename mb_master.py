#!/usr/bin/env python

import ConfigParser
import serial
import copy
import re
import os
import sys
import time
import datetime
import logging
from mb_register import MBRegister
from mb_slave import MBSlave, InvalidMessage, BadChecksum
from pretty_format import PrettyFormat, PfFloat, PfInt
from mb_formatter import CSVFormatter, GnosticFormatter, PrettyFormatter
import mb_rrd

global log
log = None

class MBMaster:
    def __init__(self, config_file="/etc/fml.conf", cl_args={}):
        if log: log.info('MBMaster config file is: %s' % repr(config_file))
        self.slaves = dict()
        # defaults for master configuration
        self.config_file = config_file
        self.times = None
        self.output_file = None
        self.appending = False
        self.output_format = None
        self.daemon = False
        self.stats = {'crc_err': 0, 'no_reply': 0, 'other_err': 0, 'iterations': 0, 'warnings': 0}
        self.formatters = []
        self.read_config_file(cl_args)
        self.output_fd = None
        self.serial = None
        self.clobber = cl_args['clobber']
        self.rrd_disable = cl_args['rrd_disable']
        # initialize rrd database
        if not self.rrd_disable:
            self.rrd = mb_rrd.MBRrd(self.config_file, self, cl_args)

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
            'output_format':    None,
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

        # Create a formatter object
        if self.output_format == 'csv':
            self.formatters.append(CSVFormatter(self))
        elif self.output_format == 'gnostic':
            self.formatters.append(GnosticFormatter(self))
        elif self.output_format == 'pretty':
            self.formatters.append(PrettyFormatter(self))
        elif self.output_format == 'none':
            self.formatters = []
        elif self.output_format is not None:
            raise ValueError("output_format should be 'pretty', 'gnostic', 'csv' or 'none', but %s was specified" % repr(self.output_format))

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
                for item in [i for i in sorted(p.items(sec)) if rexp.match(i[0]) is not None]:
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
                    pf = {'float': PfFloat(), 'int': PfInt()}[pp_type]
                    disp = False if name[0] == '*' else True
                    slave.add_register(MBRegister(address=address, name=name, mb_type=raw_type, pp_func=pp_func, pp_params=pp_params, pp_type=pp_type, pf=copy.copy(pf), display=disp))
                        
                slave.update_mb_query()
                self.add_slave(slave)
            except Exception as e:
                print "ERROR: failed add slave for section %s : %s" % (repr(sec), e)
                raise

        if log:
            s = "MBMaster loaded configuration:\n%s\n%s" % (repr(self), self.dump_config())
            for line in s.split('\n'):
                log.debug(line)

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
        for sl in sorted(self.slaves.keys()):
            s += '\n+ %s' % repr(self.slaves[sl]).replace('\n', '\n - ')
        return s

    def add_slave(self, slave):
        if not isinstance(slave, MBSlave):
            raise TypeError('must be MBSlave')
        self.slaves[slave.address] = slave

    def run(self):  
        try:
            self.open_serial_port()
        except Exception as e:
            if log: log.error('failed to open serial port: %s' % e)
            return 1

        try:
            self.open_output_file()
        except Exception as e:
            if log: log.error('failed to open output file %s: %s' % (repr(self.output_file), e))
            return 1

        if not self.appending:
            self.output_headers()

        while True:
            loop_start_time = time.time()
            if log: log.debug('fetching from slaves...')

            try:
                self.query_slaves()
                timestamp = (loop_start_time + time.time()) / 2 # average now and loop start to give most "middle" time... :s
                self.output_data(timestamp) 
                if not self.rrd_disable:
                    v = []
                    for sk, s in self.slaves.items():
                        for rk, r in s.registers.items():
                            v.append(r.get())
                    self.rrd.add_data(timestamp, self.stats['crc_err'], self.stats['no_reply'], self.stats['other_err'], v)
            except BadChecksum as e:
                if log: log.warning(str(e))
                self.stats['crc_err'] += 1
                pass
            except InvalidMessage as e:
                if log: log.warning('bad reply: %s', str(e))
                self.stats['other_err'] += 1
                pass

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
        return 0

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
        if len(self.formatters) == 0:
            self.output_fd = open('/dev/null', 'a')
        elif self.output_file is None or self.output_file == '-':
            self.output_fd = sys.stdout
        else:
            # TODO: handle multiple format types
            ext = {'pretty':'txt', 'csv':'csv', 'gnostic':'gnostic'}[self.output_format]
            self.output_file = datetime.datetime.now().strftime(self.output_file.replace('%_', ext))
            if log: log.info('output file is: %s' % self.output_file)
            if os.path.exists(self.output_file):
                self.appending = True
            self.output_fd = open(self.output_file, 'a')

    def output_headers(self):
        for f in self.formatters:
            f.output_header()

    def query_slaves(self):
        for s_add, slave in self.slaves.items():
            if log: log.debug('fetching slave address=%d, name=%s query=%s' % (s_add, slave.name, repr(slave.mb_query)))
            # write the modbus query command to all nodes connected to serial port
            slave.clear_regs()
            self.serial.write(slave.mb_query)
            self.serial.flush()
            # wait for reply
            reply = self.serial.read(1000)
            if len(reply) == 0:
                if log: log.warning('no reply from slave address=%d, name=%s' % (s_add, slave.name))
            else:
                if log: log.debug('reply from slave address=%d, name=%s : %s' % (s_add, slave.name, repr(reply)))
                slave.set_values(reply)

    def output_data(self, timestamp):
        for f in self.formatters:
            f.output_data(timestamp)

    def shutdown(self):
        # flush files and write rrd if we're doing that
        if log: log.info('MBMaster shutting down. Flushing files, writing RRD caches...')
        if isinstance(self.output_fd, file):
            if not self.output_fd.closed:
                self.output_fd.flush()
                self.output_fd.close()
        if not self.rrd_disable:
            try:
                self.rrd.update_rrd(int(time.time()))
            except:
                # we don't really care if this fails, we're closing anyway
                # if it does fail it's because there was an update in the last second
                pass

if __name__ == '__main__':
    m = MBMaster('./fml.conf')
    print repr(m)
    print m.dump_config()

