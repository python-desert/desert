===============================
Desert: DRY deserialization
===============================

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - code
      - | |latest-commit|
    * - tests
      - | |travis|
        | |codecov|
    * - package
      - | |version|
        | |wheel|
        | |supported-versions|
        | |supported-implementations|


.. |docs| image:: https://readthedocs.org/projects/desert/badge/?style=flat
    :target: https://readthedocs.org/projects/desert
    :alt: Documentation Status


.. |travis| image:: https://img.shields.io/travis/com/python-desert/desert/master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/python-desert/desert

.. |codecov| image:: https://codecov.io/github/python-desert/desert/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/python-desert/desert

.. |version| image:: https://img.shields.io/pypi/v/desert.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/pypi/desert

.. |latest-commit| image:: https://img.shields.io/github/last-commit/python-desert/desert/master
    :alt: Latest commit
    :target: https://github.com/python-desert/desert

.. |wheel| image:: https://img.shields.io/pypi/wheel/desert.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/pypi/desert

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/desert.svg
    :alt: Supported versions
    :target: https://pypi.org/pypi/desert

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/desert.svg
    :alt: Supported implementations
    :target: https://pypi.org/pypi/desert


.. end-badges


Desert generates serialization schemas for ``dataclasses`` and ``attrs`` classes. Writing
code that's DRY ("don't repeat yourself") helps avoid bugs and improve readability. Desert
helps you write code that's DRY.







Installation
============

::

    pip install desert

or with `Poetry`_

::

   poetry add desert


Usage
=========

..
    start-basic-usage

A simple example models two ``Person`` objects in a ``Car``.

.. code-block:: python



        from dataclasses import dataclass

        # Or using attrs
        # from attr import dataclass

        from typing import List

	import desert

        @dataclass
        class Person:
            name: str
            age: int

        @dataclass
        class Car:
            passengers: List[Person]

        # Load some simple data types.
        data = {'passengers': [{'name': 'Alice', 'age': 21}, {'name': 'Bob', 'age': 22}]}


        # Create a schema for the Car class.
        schema = desert.schema(Car)

        # Load the data.
        car = schema.load(data)
        assert car == Car(passengers=[Person(name='Alice', age=21), Person(name='Bob', age=22)])


..
    end-basic-usage

Documentation
=============


https://desert.readthedocs.io/


Limitations
============

String annotations and forward references inside of functions are not supported.





Acknowledgements
=================

- This package began as an extension of marshmallow-dataclass_ to add support for attrs_.


.. _Poetry: https://poetry.eustace.io
.. _marshmallow-dataclass: https://pypi.org/project/marshmallow-dataclass/
.. _attrs: http://www.attrs.org/
