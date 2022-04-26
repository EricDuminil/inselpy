from typing import List
from .insel import OneBlockModel, Template, ExistingModel, Parameter

#TODO: Add docstrings
#TODO: Add gnuplot functions

def block(name: str, *inputs: float,
          parameters: List[Parameter] = [],
          outputs: int = 1):
    return OneBlockModel(name, inputs=inputs, outputs=outputs, parameters=parameters).run()

def template(name, **parameters):
    return Template(name, **parameters).run()


def run(path):
    return ExistingModel(path).run()


def raw_run(*params):
    return ExistingModel(*params).raw_results().decode()
