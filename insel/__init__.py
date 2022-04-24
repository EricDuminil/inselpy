from .insel import OneBlockModel, Template, ExistingModel

#TODO: Add docstrings
#TODO: Add gnuplot functions

def block(name, *args, **kwargs):
    parameters = kwargs.get('parameters', [])
    outputs = kwargs.get('outputs', 1)
    return OneBlockModel(name, inputs=args, outputs=outputs, parameters=parameters).run()

def template(name, **parameters):
    return Template(name, **parameters).run()


def run(path):
    return ExistingModel(path).run()


def raw_run(*params):
    return ExistingModel(*params).raw_results().decode()
