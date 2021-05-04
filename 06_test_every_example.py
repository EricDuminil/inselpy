# coding=utf8
from subprocess import run, TimeoutExpired
import tempfile
from pathlib import Path

examples = Path('/usr/local/insel/examples/')

def replace_gnuplot(line):
    return line.replace("'insel.gnu'", f"'{dummy_gnuplot_path}'")


with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_dir = Path(tmp_dir)

    dummy_gnuplot_path = tmp_dir / 'dummy.gnu'
    with open(dummy_gnuplot_path, 'w') as out:
        out.write('set terminal unknown')

    for vseit_path in examples.glob('**/*.vseit'):
        tmp_vseit_path = tmp_dir / vseit_path.name
        with open(tmp_vseit_path, 'w') as tmp_vseit:
            with open(vseit_path) as vseit:
                for line in vseit:
                    tmp_vseit.write(replace_gnuplot(line))
        try:
            run(["insel", tmp_vseit_path], cwd=tmp_dir, timeout=10)
        except TimeoutExpired:
            print("Timeout")
