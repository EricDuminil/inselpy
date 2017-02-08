from model import *

class OneBlockModel(Model):
  def __init__(self, name = '', inputs = [], parameters = []):
    self.name = name
    self.parameters = parameters
    self.inputs = inputs

  def content(self):
    lines = []
    input_ids = []
    for i,arg in enumerate(self.inputs, 1):
      input_ids.append("%s.1" % i)
      lines.append("s %d CONST" % i)
      lines.append("p %d" % i)
      lines.append("\t%r" % arg)

    lines.append("s %d %s %s" % (len(self.inputs)+1,self.name.upper(), " ".join(input_ids)))

    lines.append("s %d SCREEN %d.1" % (len(self.inputs)+2, len(self.inputs)+1))
    return "\n".join(lines)
