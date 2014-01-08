#!/usr/bin/env python

import inspect

pp_functions = dict()

class NotRegistered(Exception):
    def __init__(self, fname):
        self.fname = fname
    def __str__(self):
        return 'function not registered: "%s"' % repr(self.fname)

class ParameterError(Exception):
    def __init__(self, fname, expected, got):
        self.fname = fname
        self.expected = expected
        self.got = got
    def __str__(self):
        return 'function "%s" expected %d param(s) but got %d' % (self.fname, self.expected, self.got)

def register(f):
    """ register a post-processing function """
    global pp_functions
    pp_functions[f.func_name] = (f, len(inspect.getargspec(f).args)-1, inspect.getargspec(f).args)

def post_process(fname, data, *params):
    """ call a [previously registered] post-processing function by name
        with specified data value and option parameters
    """
    global pp_functions
    if fname not in pp_functions.keys():
        raise NotRegistered(fname)
    if len(params) != pp_functions[fname][1]:
        raise ParameterError(fname, pp_functions[fname][1], len(params))
    a = [data]
    a.extend(params)
    return pp_functions[fname][0](*a)

def check(fname, *params):
    """ check that a named post-processing function is registered and that 
        specified parameters are ok to use 
        raises exceptions on error: NotRegistered & ParameterError
    """
    global pp_functions
    if fname == '':
        return True
    if fname not in pp_functions.keys():
        raise NotRegistered(fname)
    if len(params) != pp_functions[fname][1]:
        raise ParameterError(fname, pp_functions[fname][1], len(params))
    return True

def thermister_to_celcius(data, B, T0, R0):
    # R = (V*R_Balance)/(3.3-V), where V = ((data*4.096)/2048).
    # temp in C = (1.0/(1.0/T0+(1.0/B)*log(R/R0))) - 273.15
    # R0, B, T0 are constants from the circuit / components
    # simplified formulae and generated code from mathomatic.  Assuming R_Balance is the same thing as R0
    V = float(data)/500.0
    R = (V*float(R0)/((33.0/10.0) - V))
    return (1.0/(1.0/float(T0)+(1.0/float(B))*math.log(R/float(R0)))) - 273.15

def scale_voltage(data, R1, R2):
    # Conversion from a data reading (16 bit number) into the voltage is:
    # Actual input voltage = ((R1+R2)/(R1))*((data*4.096)/2047)
    # Where R1 and R2 are the input resistor values which will vary with different ranges.
    # simplified by mathomatic
    return ((float(data)*4.096/2047)*float(R1+R2))/float(R1)

def scale_current(data):
    # The current varies around a 2V midpoint (set by an accurate voltage reference). 
    # If the value is >2V the it is input current, if it is <2V then it is output current.
    # The current transducer puts out 100mV per Amp. So conversion is:
    # Actual input current = (((data*4.096)/2047)-2)/0.1
    #return (((data*4.096)/2047)-2)/0.1
    return (((float(data)*4.096)/2047.))/0.1

register(thermister_to_celcius)
register(scale_voltage)
register(scale_current)

if __name__ == '__main__':
    def linear_scale(data, factor):
        return data * factor

    def c_to_k(data):
        return data - 274.15
        
    register(linear_scale)
    register(c_to_k)

    print 'c_to_k(18) -> %.1f' % post_process('c_to_k', 18)
    print 'linear_scale(20, 3) -> %.1f' % post_process('linear_scale', 20, 3)

    check('c_to_k')
    print 'c_to_k check ok'
    check('linear_scale', 3.14)
    print 'linear_scale check ok'

    try:
        check('unregistered_function_name')
    except NotRegistered as e:
        print e
        print "successfully detected unregistered function"

    try:
        check('linear_scale')
    except ParameterError as e:
        print e
        print "successfully detected incorrect number of parameters"
    try:
        check('c_to_k', 3)
    except ParameterError as e:
        print e
        print "successfully detected incorrect number of parameters: %s" 

        
