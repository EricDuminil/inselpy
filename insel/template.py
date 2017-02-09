from model import *
from os import path
import re


class Template(Model):
    dirname = path.join(path.dirname(__file__), '../templates')
    pattern = re.compile('\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w \.]*))?\$')

    def __init__(self, name='', **parameters):
        self.name = name
        self.parameters = self.add_defaults_to(parameters)

    def template_filename(self):
        f = path.join(Template.dirname, '%s.insel' % self.name)
        if path.exists(f):
            return f
        else:
            raise Exception("No template in %s" % f)

    def replace(self, string):
        var_name, index, default = string.groups()
        var_name = var_name.strip()
        if var_name in ['longitude', 'timezone']:
            print "WARNING : Make sure to use INSEL convention for {0}. Rename to insel_{0} to remove warning".format(var_name)
        if var_name in self.parameters:
            if index:
                return str(self.parameters[var_name][int(index)])
            else:
                return str(self.parameters[var_name])
        elif default:
            return default
        else:
            raise Exception(
                "UndefinedValue for '%s' in %s.insel template" %
                (var_name, self.name))

    def add_defaults_to(self, parameters):
        defaults = {'bp_folder': path.join(Insel.dirname, "data", "bp")}
        if 'longitude' in parameters:
            defaults['insel_longitude'] = -parameters['longitude']
        if 'timezone' in parameters:
            defaults['insel_timezone'] = (24 - parameters['timezone']) % 24
        defaults.update(parameters)
        return defaults

    def content(self):
        with open(self.template_filename()) as template:
            content = template.read()
            content = re.sub(Template.pattern, self.replace, content)
            return content
