#!/usr/bin/env python

import inspect

pp_functions = dict()

def add_pp_function(f):
    global pp_functions
    pp_functions[f.func_name] = (f, len(inspect.getargspec(f).args)-1, inspect.getargspec(f).args)

def post_process(fname, data, *params):
    global pp_functions
    if fname not in pp_functions.keys():
        raise Exception('unknown post-processing function name: %s' % fname)
    if len(params) != pp_functions[fname][1]:
        raise Exception('incorrect number of parameters for function %s (wanted %d, got %d)' % (fname, pp_functions[fname][1], len(params)))
    a = [data]
    a.extend(params)
    return pp_functions[fname][0](*a)

if __name__ == '__main__':
    def linear_scale(data, factor):
        return data * factor

    def c_to_k(data):
        return data - 274.15
        
    add_pp_function(linear_scale)
    add_pp_function(c_to_k)

    print 'c_to_k(18) -> %.1f' % post_process('c_to_k', 18)
    print 'linear_scale(20, 3) -> %.1f' % post_process('linear_scale', 20, 3)

    try:
        print 'value from undefined function: %s' % post_process('undef_fn', 10)
    except Exception as e:
        print 'expected exception:'
        print 'exception:  %s / %s' % ( type(e), e )

        
