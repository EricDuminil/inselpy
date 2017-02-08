from model import *
from os import path
import re

class Template(Model):
  dirname = path.join(path.dirname(__file__), 'templates')
  pattern = re.compile('\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w \.]*))?\$')

  def __init__(self, name = '', **parameters):
    self.name = name
    self.parameters = parameters

  def template_filename(self):
    f = path.join(Template.dirname, '%s.insel' % self.name)
    if path.exists(f):
      return f
    else:
      raise Exception("No template in %s" % f)

  def replace(self, string):
    var_name, index, default = string.groups()
    var_name = var_name.strip()
    if var_name in self.parameters:
      if index:
        return str(self.parameters[var_name][int(index)])
      else:
        return str(self.parameters[var_name])
    elif default:
      return default
    else:
      raise Exception("UndefinedValue for %s in %s" % (var_name, self.name))

  def content(self):
    with open(self.template_filename()) as template:
      content = template.read()
      content = re.sub(Template.pattern, self.replace, content)
      return content
