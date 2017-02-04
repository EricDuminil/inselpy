import os
import subprocess
import tempfile
import re

class Insel:
  dirname = "/usr/local/INSEL/resources/"
  command = "./insel"
  extension = ".insel"
  regexp = re.compile('Running insel [\d\w \.]+ \.\.\.\s+([^\*]*)Normal end of run', re.I | re.DOTALL)

#TODO: use private methods
class Model:
  def run(self):
    raw = self.raw_results()
    match = Insel.regexp.search(raw)
    if match:
      output = match.group(1)
      floats = self.extract([self.parse_line(line) for line in output.split("\n") if line])
      return floats
    else:
      raise Exception("Problem with INSEL : %s" % raw)

  def parse_line(self, line):
      return self.extract([float(x) for x in line.split() if x])

  def extract(self, array):
    if len(array) == 1:
      return array[0]
    else:
      return array

  def raw_results(self):
    #TODO: come back to cwd
    os.chdir(Insel.dirname)
    with self.tempfile() as file:
      file.write(self.content())
      file.flush()
      os.fsync(file.fileno())
      var = subprocess.check_output([Insel.command, file.name], shell = False)
    return var

  def tempfile(self):
    return tempfile.NamedTemporaryFile(mode = 'w+', suffix = Insel.extension, prefix = 'python_')

  def content(self):
    raise Exception("IMPLEMENT ME")
