from one_block_model import OneBlockModel
from template import Template

def block(name, *args):
    return OneBlockModel(name, inputs = args).run()

def template(name, **parameters):
    return Template(name, **parameters).run()
