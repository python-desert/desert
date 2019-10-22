========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |latest-commit|

.. |docs| image:: https://readthedocs.org/projects/desert/badge/?style=flat
    :target: https://readthedocs.org/projects/desert
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.com/python-desert/desert.svg?branch=master
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
    :target: https://img.shields.io/github/commits-since/python-desert/desert/v0.1.1.svg

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

Deserialize to objects while staying DRY.


Installation
============

::

    pip install desert


Usage
=========

..

    start-basic-usage

To use Desert in a project:

.. code-block:: python

        from dataclasses import dataclass

        # Or, using `attrs`,
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
        data = {'passengers': [{'name': 'Alice': 'age': 21}, {'name': 'Bob', 'age': 22}]}


        # Create a schema for the Car object.
        schema = desert.schema(Car)

        # Load the data.
        car = schema.load(car)
        assert car == Car(passengers=[Person(name='Alice', age=21), Person(name='Bob', age=22)])


..

    end-basic-usage

Documentation
=============


https://desert.readthedocs.io/
