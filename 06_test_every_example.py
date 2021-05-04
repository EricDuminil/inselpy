# coding=utf8
from subprocess import TimeoutExpired, check_output
import tempfile
from pathlib import Path
import unittest
import re

examples = Path('/usr/local/insel/examples/')

warning = re.compile('^[EFW]\d{5}.*?$', re.M)
normal_run = re.compile(
    'Running insel [\d\w \.]+ \.\.\.\s+([^\*]*)Normal end of run',
    re.I | re.DOTALL)

def replace_gnuplot(line, new_gnu):
    return line.replace("'insel.gnu'", f"'{new_gnu}'")

class TestExamples(unittest.TestCase):
    def test_all(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)

            dummy_gnuplot_path = tmp_dir / 'dummy.gnu'
            with open(dummy_gnuplot_path, 'w') as out:
                out.write('set terminal unknown')

            for vseit_path in examples.glob('**/*.vseit'):
                tmp_vseit_path = tmp_dir / vseit_path.name
                print(vseit_path.name)
                with self.subTest(msg=vseit_path.name):
                    with open(tmp_vseit_path, 'w') as tmp_vseit:
                        with open(vseit_path) as vseit:
                            for line in vseit:
                                tmp_vseit.write(replace_gnuplot(line, dummy_gnuplot_path))
                    try:
                        warnings = []
                        result = check_output(["insel", tmp_vseit_path],
                                              cwd=tmp_dir,
                                              timeout=10).decode()
                        for problem in warning.findall(result):
                            print('  ', problem)
                            warnings.append(problem)
                        self.assertTrue(len(warnings) == 0,
                                        f"Errors/Warnings were found during execution of {vseit_path}")
                    except TimeoutExpired:
                        self.fail(f"Timeout for {vseit_path}")

if __name__ == '__main__':
    unittest.main()
