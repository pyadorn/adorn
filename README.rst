Adorn
======

|PyPI| |Status| |Python Version| |License|

|Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/adorn.svg
   :target: https://pypi.org/project/adorn/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/adorn.svg
   :target: https://pypi.org/project/adorn/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/adorn
   :target: https://pypi.org/project/adorn
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/adorn
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License
.. |Tests| image:: https://github.com/pyadorn/adorn/workflows/Tests/badge.svg
   :target: https://github.com/pyadorn/adorn/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/pyadorn/adorn/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/pyadorn/adorn
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


Features
--------
``adorn`` is a configuration tool for python code.

``adorn`` can currently

* instantiate an object
* check that a config can instantiate an object


Example
-------

.. code-block:: python

   from adorn.orchestrator.base import Base
   from adorn.params import Params
   from adorn.unit.complex import Complex
   from adorn.unit.constructor_value import ConstructorValue
   from adorn.unit.parameter_value import ParameterValue
   from adorn.unit.python import Python


   @Complex.root()
   class Example(Complex):
      pass

   @Example.register(None)
   class Parent(Example):
       def __init__(self, parent_value: str) -> None:
           super().__init__()
           self.parent_value = parent_value


   @Parent.register("child")
   class Child(Parent):
       def __init__(self, child_value: int, **kwargs) -> None:
           super().__init__(**kwargs)
           self.child_value = child_value


   base = Base(
       [
           ConstructorValue(),
           ParameterValue(),
           Example(),
           Python()
       ]
   )

   params = Params(
           {
               "type": "child",
               "child_value": 0,
               "parent_value": "abc"
           }
   )

   # well specified configuration
   # we can type check from any level in the
   # class hierarchy
   assert base.type_check(Example, params) is None
   assert base.type_check(Parent, params) is None
   assert base.type_check(Child, params) is None

   # instantiate
   # we can instantiate from any level in the
   # class hierarchy
   example_obj = base.from_obj(
       Example,
       params
   )

   assert isinstance(example_obj, Child)


   parent_obj = base.from_obj(
       Parent,
       params
   )

   assert isinstance(parent_obj, Child)


   child_obj = base.from_obj(
       Child,
       params
   )

   assert isinstance(child_obj, Child)



Installation
------------

You can install *Adorn* via pip_ from PyPI_:

.. code:: console

   $ pip install adorn



Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `Apache 2.0 license`_,
*Adorn* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _Apache 2.0 license: https://opensource.org/licenses/Apache-2.0
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/pyadorn/adorn/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://adorn.readthedocs.io/en/latest/usage.html
