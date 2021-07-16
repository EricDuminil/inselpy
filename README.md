# INSELpy

This module allows to execute INSEL models from Python, and can be used to write unit tests for INSEL blocks and models.

```python
>>> import insel
>>> insel.block('sum', 1, 2)
3.0
>>> insel.block('do', parameters = [1, 10, 1])
[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
>>> insel.template('a_times_b', a=4, b=5)
20.0
>>> insel.run('/usr/local/insel/examples/meteorology/sunae.vseit')
[]
```

