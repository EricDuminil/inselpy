from one_block_model import OneBlockModel
from template import Template

def block(name, parameters= [], *args):
    print "name %s" % name
    if args:
        print "inputs %r" % args
    if parameters:
        print "parameters %r" % parameters 
    return OneBlockModel(name, inputs = args, parameters = parameters).run()

def template(name, **parameters):
    return Template(name, **parameters).run()
