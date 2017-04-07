from .insel import OneBlockModel
from .insel import Template


def block(name, *args, **kwargs):
    parameters = kwargs.get('parameters', [])
    return OneBlockModel(name, inputs=args, parameters=parameters).run()


def template(name, **parameters):
    return Template(name, **parameters).run()
