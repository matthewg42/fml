#!/usr/bin/env python

import re

class PrettyFormat:
    def __init__(self, width, align='left', fmt='s', pad=''):
        """ If you want to specify precision for floats, prefix that on the fmt, without the width
            i.e. PrettyFormat(width=10, fmt='.4f') -> %10.4f
        """
        if align not in ['left','right']:
            raise ValueError("align must be 'left' or 'right'")
        if re.match('^((\.\d+)?f)|[sd]$', fmt) == None:
            raise ValueError("fmt must be 's', 'd', 'f', or '.nf' (where n in an int)")
        if pad not in ['','0']:
            raise ValueError("pad must be '' or '0'")
        if not isinstance(width, int):
            raise ValueError('width must be an int')
        self.width = width
        self.align = align
        self.fmt = fmt
        self.pad = pad

    def __repr__(self):
        return "PrettyFormat(width=%d, align='%s', fmt='%s', pad='%s')@%s" % (self.width, self.align, self.fmt, self.pad, hex(id(self)))

    def fmtstr(self, string=False):
        """ returns a printf style format string for this PrettyFormat, 
            If string=True then return as 's' format with the proper width and alignment instead
            e.g. width=10, align='left', fmt='d', pad='0', string=False -> '%-010d'
            e.g. width=10, align='left', fmt='d', pad='0', string=True -> '%-10s'
        """
        fmt = self.fmt
        pad = self.pad
        align = {'left':'-','right':''}[self.align]
        if string:
            fmt = 's'
            pad = ''
        return '%%%s%s%d%s'  % (align, pad, self.width, fmt)

    def out(self, value, string=False):
        try:
            r = self.fmtstr(string) % value
        except:
            r = self.fmtstr(True) % '#ERR'
            pass
        return r

    def underline(self, char='_'):
        return char * self.width

    def expand_to_fit(self, s):
        if len(s) > self.width:
            self.width = len(s)
           

# define some ready-to-use formats
PfInt       = PrettyFormat(width=6,  align='right', fmt='d')
PfFloat     = PrettyFormat(width=9,  align='right', fmt='.3f')
PfTimestamp = PrettyFormat(width=23, align='left',  fmt='s')

if __name__ == '__main__':
    import datetime
    from mb_register import MBRegister
    
    for f in [PrettyFormat(10),
              PrettyFormat(6,  align='right', fmt='d', pad='0'),
              PrettyFormat(10, fmt='.3f', pad=''),
              PrettyFormat(10, align='right', fmt='.3f', pad=''),
              PrettyFormat(8,  align='right', fmt='d', pad='0') ]:
        print "f is: " + repr(f)
        print "f.fmtstr():            '%s'" % f.fmtstr()
        print "f.fmtstr(string=True): '%s'" % f.fmtstr(True)
        print "f.out(3):              '%s'" % f.out(3)
        print "f.out(3):              '%s'" % f.out(300)
        print "f.out(3):              '%s'" % f.out(123456)
        print "f.underline():         '%s'" % f.underline()
        print ""

    print "PfInt        -1234 : '%s'" % PfInt.out(-1234)
    print "PfFloat 3.14159265 : '%s'" % PfFloat.out(3.14159265)
    print "PfTimestamp [now]  : '%s'" % PfTimestamp.out(datetime.datetime.now().strftime("%Y-%m-%d %T.%f")[:-3])
    print ""

