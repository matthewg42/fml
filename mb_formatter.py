#!/usr/bin/env python

import time
import datetime

class CSVFormatter:
    def __init__(self, master):
        self.master = master

    def output_header(self):
        a = ['timestamp']
        for s_add, slave in sorted(self.master.slaves.items()):
            for r_add, register in sorted(slave.registers.items()):
                if register.display:
                    a.append('%s/%s' % ( slave.name.replace(',','\\,'), register.name.replace(',','\\,')))
        self.master.output_fd.write(",".join(a) + "\n")

    def output_data(self, timestamp):
        a = [datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %T.%f")[:-3]]
        for s_add, slave in sorted(self.master.slaves.items()):
            for r_add, register in sorted(slave.registers.items()):
                if register.display:
                    a.append(register.pretty_value().replace(' ',''))
        self.master.output_fd.write(",".join(a) + "\n")

class GnosticFormatter:
    def __init__(self, master):
        self.master = master

    def output_header(self):
        self.master.output_fd.write("GNOSTIC-DATA-PROTOCOL-VERSION=1.0\nDELIMITER=;\nEND-HEADER\n")

    def output_data(self, timestamp):
        for s_add, slave in sorted(self.master.slaves.items()):
            for r_add, register in sorted(slave.registers.items()):
                if register.display:
                    self.master.output_fd.write('%.3f;%s;%s\n' % ( slave.last_fetched, register.pretty_value().replace(' ',''), register.name ))

class PrettyFormatter:
    def __init__(self, master, gutter=' '):
        self.master = master
        self.gutter = gutter

    def output_header(self):
        h1 = []
        h2 = []
        ul = []
        h1.append(' ' * 24)
        h2.append('%-24s' % 'Time')
        ul.append('_' * 24)
        for s_add, slave in sorted(self.master.slaves.items()):
            s_begin = len(self.gutter.join(h2)) + len(self.gutter)
            for r_add, register in sorted(slave.registers.items()):
                h2.append(register.pretty_header())
                ul.append(register.pf.underline())
            s_end = len(self.gutter.join(h2))
            sl_text = str.center(slave.name[:s_end-s_begin], s_end-s_begin, '-')
            if sl_text[:1] == '-':
                sl_text = '<' + sl_text[1:]
            if sl_text[-1:] == '-':
                sl_text = sl_text[:-1] + '>'
            h1.append(sl_text)
        self.master.output_fd.write(self.gutter.join(h1) + "\n")
        self.master.output_fd.write(self.gutter.join(h2) + "\n")
        self.master.output_fd.write(self.gutter.join(ul) + "\n\n")

    def output_data(self, timestamp):
        a = ['%-24s' % datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %T.%f")[:-3]]
        for s_add, slave in sorted(self.master.slaves.items()):
            for r_add, register in sorted(slave.registers.items()):
                if register.display:
                    a.append(register.pretty_value())
        self.master.output_fd.write(self.gutter.join(a) + "\n")

