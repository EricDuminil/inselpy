from .insel import OneBlockModel
from .insel import Template


def block(name, *args, **kwargs):
    parameters = kwargs.get('parameters', [])
    outputs = kwargs.get('outputs', 1)
    return OneBlockModel(name, inputs=args, outputs=outputs, parameters=parameters).run()


def template(name, **parameters):
    return Template(name, **parameters).run()
