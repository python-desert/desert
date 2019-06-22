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
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-marshmallow-attrs/badge/?style=flat
    :target: https://readthedocs.org/projects/python-marshmallow-attrs
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.org/adamboche/python-marshmallow-attrs.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/adamboche/python-marshmallow-attrs

.. |codecov| image:: https://codecov.io/github/adamboche/python-marshmallow-attrs/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/adamboche/python-marshmallow-attrs

.. |version| image:: https://img.shields.io/pypi/v/marshmallow-attrs.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/pypi/marshmallow-attrs

.. |commits-since| image:: https://img.shields.io/github/commits-since/adamboche/python-marshmallow-attrs/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/adamboche/python-marshmallow-attrs/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/marshmallow-attrs.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/pypi/marshmallow-attrs

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/marshmallow-attrs.svg
    :alt: Supported versions
    :target: https://pypi.org/pypi/marshmallow-attrs

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/marshmallow-attrs.svg
    :alt: Supported implementations
    :target: https://pypi.org/pypi/marshmallow-attrs


.. end-badges

Marshmallow schemas for attrs classes

* Free software: MIT license

Installation
============

::

    pip install marshmallow-attrs

Documentation
=============


https://python-marshmallow-attrs.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
