# INSELpy

This module allows to execute [INSEL](https://insel.eu/) models from Python, and can be used to write unit tests for INSEL blocks and models.

## Single blocks

It can run single blocks, with the specified inputs, parameters and number of outputs:
```python
>>> import insel
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
```

## INSEL templates

INSELpy can also run INSEL templates:
```
% Calculates a*b
s 1 MUL  3.1 2.1
s 2 CONST
p 2
           $a || 3$
s 3 CONST
p 3
           $b || 3$
s 4 SCREEN  1.1
p 4
    '*'
```

Templates will be searched inside the 'templates/' folder, relative to the current working directory.

Either in the REPL:

```python
>>> insel.template('a_times_b', a=7, b=3)
21.0
>>> insel.template('photovoltaic/i_sc', pv_id='008823', temperature=25, irradiance=1000)
5.87388
```

or in complete scripts:

```python
import insel

name = 'Roma'
lat = 41.8
lon = 12.58
timezone = 1

irradiances = insel.template('weather/get_irradiance_profile', latitude=lat, longitude=lon)
print(irradiances)
# => [71.0, 106.0, 158.0, 208.0, 251.0, 275.0, 286.0, 257.0, 196.0, 137.0, 84.0, 63.0]

print((insel.template('weather/average_irradiance_on_tilted_surface',
                      tilt=30,
                      azimuth=180,
                      irradiance_profile=irradiances,
                      latitude=lat,
                      longitude=lon,
                      timezone=timezone)))
# => 195.8578
```
## Vseit models

Insel graphical models (Vseit) are valid templates. Constants defined by `Define global constant` block can be modified in Python.

If no value is specified in Python, the value defined in the block will be used by default.

```
>>> insel.template('constants/x_plus_y.vseit')
3.0
>>> insel.template('constants/x_plus_y.vseit', x=5)
7.0
>>> insel.template('constants/x_plus_y.vseit', x=5, y=5)
10.0
```

If the Vseit model contains a PLOT block, it will be deactivated by default. In order to launch gnuplot anyway, `insel.template('model.vseit', gnuplot=True)` can be used.

## INSEL models

It can also simply run complete models:
```python
>>> insel.run('/usr/local/insel/examples/meteorology/sunae.vseit')
[]
```

