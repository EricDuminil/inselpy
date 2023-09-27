from pathlib import Path
from typing import List

from .existing_model import ExistingModel

#  To allow from insel import Insel, InselError in tests:
from .insel import Insel as Insel
from .insel import Parameter
from .insel_error import InselError as InselError
from .one_block_model import OneBlockModel
from .template import Template
from .plot import Plot

__version__ = "0.0.9b"


def block(
    name: str, *inputs: float, parameters: List[Parameter] = [], outputs: int = 1
):
    """
    Returns the output of INSEL block *name*, with the given inputs and parameters.
    One output is returned by default, but more can be returned if desired.

    * If the block returns one value, this function returns a float.
    * If the block returns multiple values on one line, this function returns a list of floats.
    * If the block returns multiple lines, this function returns a list of floats.
    * If the block returns multiple values on multiple lines,
         this function returns a list of list of floats.

    >>> insel.block('pi')
    3.141593
    >>> insel.block('sum', 2, 3)
    5.0
    >>> insel.block('do', parameters=[1, 10, 1])
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    >>> insel.block('do', parameters=[1, 10, 1])
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    >>> insel.block('gain', 2, 5, 7, parameters=[3], outputs=3)
    [6.0, 15.0, 21.0]
    """
    return OneBlockModel(
        name, inputs=inputs, outputs=outputs, parameters=parameters
    ).run()


def template(template_path: str | Path, **parameters):
    """
    Returns the output of INSEL template found at template_path,
    after substituting parameters inside the template.

    If template_path is an absolute path, the corresponding template will be used.
    If template_path is a relative path, the template will be searched in templates/ folder.

    Templates can either be .insel or .vseit files.
    If template_path has no extension, '.insel' will be appended by default.

    Parameters can either be:
        * INSEL C constants ("C XYZ 123")
        * Vseit constants ("Define global constant")
        * $ XYZ || 123 $ placeholders.

    Values can either be:
        * integers
        * floats
        * strings
        * lists

    >>> insel.template('a_times_b', a=7, b=3)
    21.0
    >>> insel.template('photovoltaic/i_sc',
          pv_id='008823', temperature=25, irradiance=1000)
    5.87388
    >>> insel.template('constants/x_plus_y.vseit', x=5, y=5)
    10.0
    """
    return Template(template_path, **parameters).run()

def plot(template_path, **parameters):
    return Plot(template_path, **parameters).run()


def run(path: Path):
    """Returns the output of INSEL model found at path, without
    substituting any parameter.
    The output is parsed, and returned as float, list of floats or list of list of floats.

    >>> insel.run('templates/one_to_ten.insel')
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    """
    return ExistingModel(path).run()


def raw_run(*params) -> str:
    """Returns the output of INSEL model found at path, without
    substituting any parameter.
    The output is returned as is, without being parsed.

    >>> print(insel.raw_run('templates/one_to_ten.insel'))
    Compiling one_to_ten.insel ...
    0 errors, 0 warnings
    Running INSEL 8.3.0.9b ...
        1
        2
        3
        4
        5
        6
        7
        8
        9
        10
    Normal end of run
    """
    return ExistingModel(*params).raw_results()
