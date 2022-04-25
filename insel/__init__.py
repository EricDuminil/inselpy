from typing import List
from .insel import OneBlockModel, Template, ExistingModel, Parameter

#TODO: Add docstrings
#TODO: Add gnuplot functions

def block(name: str, *args: float, **kwargs):
    parameters: List[Parameter] = kwargs.get('parameters', [])
    outputs: int = kwargs.get('outputs', 1)
    return OneBlockModel(name, inputs=args, outputs=outputs, parameters=parameters).run()

def template(name, **parameters):
    return Template(name, **parameters).run()


def run(path):
    return ExistingModel(path).run()


def raw_run(*params):
    return ExistingModel(*params).raw_results().decode()
