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

        
