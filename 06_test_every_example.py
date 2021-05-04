# coding=utf8
from subprocess import TimeoutExpired, check_output
import tempfile
from pathlib import Path
import unittest
import re

TIMEOUT = 10

examples = Path('/usr/local/insel/examples/')

warning = re.compile(r'^[EFW]\d{5}.*?$', re.M)
normal_run = re.compile(
    r'Running insel [\d\w \.]+ \.\.\.\s+([^\*]*)Normal end of run',
    re.I | re.DOTALL)


def replace_gnuplot(line, new_gnu):
    return line.replace("'insel.gnu'", f"'{new_gnu}'")


def create_temp_vseit(vseit_path):
    tmp_vseit_path = TMP_DIR / vseit_path.name
    print(vseit_path.name)
    with open(tmp_vseit_path, 'w') as tmp_vseit:
        with open(vseit_path) as vseit:
            for line in vseit:
                tmp_vseit.write(replace_gnuplot(line, NULL_GNUPLOT))
    return tmp_vseit_path


class TestExamples(unittest.TestCase):
    def test_all(self):
        for vseit_path in examples.glob('**/*.vseit'):
            tmp_vseit_path = create_temp_vseit(vseit_path)
            with self.subTest(msg=vseit_path.name):
                try:
                    warnings = []
                    result = check_output(["insel", tmp_vseit_path],
                                          cwd=vseit_path.parent,
                                          timeout=TIMEOUT).decode()
                    for problem in warning.findall(result):
                        print('  ', problem)
                        warnings.append(problem)
                    if len(warnings) > 0:
                        self.fail("Errors/Warnings were found.\n" + result)
                except TimeoutExpired:
                    self.fail(f"Timeout for {vseit_path}")


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp_dir:
        TMP_DIR = Path(tmp_dir)

        NULL_GNUPLOT = TMP_DIR / 'dummy.gnu'
        with open(NULL_GNUPLOT, 'w') as out:
            out.write('set terminal unknown')

        unittest.main()
