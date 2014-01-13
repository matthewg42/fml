#!/usr/bin/env python

import rrdtool
import os
import re
import logging
import ConfigParser
import mb_master

global log
log = None

class BadSignature(Exception):
    def __init__(self, database_file, signature_file, extra=None):
        self.database_file = database_file
        self.signature_file = signature_file
        self.extra = extra
    def __str__(self):
        s = 'rrd database %s does not match signature file %s' % (
                    repr(self.database_file), 
                    repr(self.signature_file))
        if self.extra is not None: s += ' - ' + self.extra
        return s

class MBRrd:
    def __init__(self, config_file, master, cl_args={}):
        if log: log.debug('Creating MNRrd(config_file=%s, cl_args=%s' % (repr(config_file), repr(cl_args)))
        self.config_file = config_file
        self.database_file = None
        self.heartbeat = None
        self.update_interval = None
        self.sig_file = None
        self.dss = []
        self.rras = []
        self.read_config_file(cl_args)
        self.signature_file = re.sub(r'\.rrd$', r'.sig', self.database_file)
        self.add_dss(master)
        # If the database file doesn't exist, we can safely create it.
        if not os.path.exists(self.database_file):
            self.create_database()
        # this raises a BadSignature exception if the sig doesn't match the database
        self.check_signature()
            

    def __repr__(self):
        s = 'MBRrd(config_file=%s)\n' % (repr(self.config_file))
        s += '\n'.join(self.dss) + '\n'
        s += '\n'.join(self.rras)
        return s

    def add_dss(self, master):
        for s_add, slave in sorted(master.slaves.items()):
            for r_add, register in sorted(slave.registers.items()):
                if register.name[0] != '*':
                    # DS:Ch1Temp1:GAUGE:120:-20:80
                    s = 'DS:r%d_%d:GAUGE:%s:U:U' % (s_add, r_add, self.heartbeat)
                    if log: log.debug('created def: %s' % s)
                    self.dss.append(s)

    def read_config_file(self, cl_args):
        p = ConfigParser.SafeConfigParser( {
            'database_file': '/var/lib/fml/fml.rrd',
            'heartbeat': '20',
            'update_interval': '10',
            'xff': '0.5',
        } )
        p.read(self.config_file)
        self.database_file = p.get('rrd','database_file')
        self.heartbeat = p.getint('rrd','heartbeat')
        self.update_interval = p.getint('rrd','update_interval')

        # now read the rrd_archive sections
        for sec in [s for s in p.sections() if s[:12] == 'rrd_archive_']:
            try:
                archive_id = int(sec[12:])
                duration = p.getint(sec, 'duration')
                samples = p.getint(sec, 'samples')
                xff = p.getfloat(sec, 'xff')
                rows = duration / (samples*self.update_interval)
                rra = 'RRA:AVERAGE:%s:%d:%d' % (xff, samples, rows)
                if log: log.debug('created rra: %s', rra)
                self.rras.append(rra)
            except Exception as e:
                if log: log.error('exception: %s / %s' % ( type(e), e))

    def create_database(self):
        a = [self.database_file]
        a = a + self.dss + self.rras
        if log: log.debug('rrdtool.create(%s)' % ", ".join([repr(i) for i in a]))
        rrdtool.create(*a)
        if os.path.exists(self.signature_file): os.remove(self.signature_file)
        with open(self.signature_file, 'w') as f:
            f.write(self.signature())

    def signature(self):
        return '\n'.join(self.dss + self.rras) + '\n'

    def check_signature(self):
        # quick and dirty slurping...
        s = open(self.signature_file, 'r').read()
        sig = self.signature()
        
        if s != sig:
            raise BadSignature(self.database_file, self.signature_file)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s')
    log = logging.getLogger('mb_rrd.py')
    log.setLevel(logging.DEBUG)
    mb_master.log = log
    f = 'fml.conf'
    m = mb_master.MBMaster(f)
    r = MBRrd(f, m)
    print repr(r)

