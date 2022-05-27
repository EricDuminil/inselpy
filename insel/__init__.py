from typing import List
from .insel import OneBlockModel, Template, ExistingModel, Parameter, Insel

# TODO: Add docstrings
# TODO: Add gnuplot functions


def block(name: str, *inputs: float,
          parameters: List[Parameter] = [],
          outputs: int = 1):
    """
    Returns the output of INSEL block *name*, with the given inputs and parameters.
    One output is returned by default, but more can be returned if desired.

    * If the block returns one value, this function returns a float.
    * If the block returns multiple values on one line, this function returns a list of floats.
    * If the block returns multiple lines, this function returns a list of floats.
    * If the block returns multiple values on multiple lines, this function returns a list of list of floats.

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
    return OneBlockModel(name, inputs=inputs, outputs=outputs, parameters=parameters).run()


def template(template_path, **parameters):
    """
    Returns the output of INSEL template found at template_path,
    after substituting parameters inside the template.

    If template_path is an absolute path, the corresponding template will be used.
    If template_path is a relative path, the template will be searched in templates/ folder.


    >>> insel.template('a_times_b', a=7, b=3)
    21.0
    >>> insel.template('photovoltaic/i_sc',
          pv_id='008823', temperature=25, irradiance=1000)
    5.87388
    """
    return Template(template_path, **parameters).run()


def run(path):
    return ExistingModel(path).run()


def raw_run(*params):
    return ExistingModel(*params).raw_results().decode()
