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

.. |docs| image:: https://readthedocs.org/projects/marshmallow-attrs/badge/?style=flat
    :target: https://readthedocs.org/projects/marshmallow-attrs
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.org/adamboche/marshmallow-attrs.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/adamboche/marshmallow-attrs

.. |codecov| image:: https://codecov.io/github/adamboche/marshmallow-attrs/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/adamboche/marshmallow-attrs

.. |version| image:: https://img.shields.io/pypi/v/marshmallow-attrs.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/pypi/marshmallow-attrs

.. |commits-since| image:: https://img.shields.io/github/commits-since/adamboche/marshmallow-attrs/v0.1.1.svg
    :alt: Commits since latest release
    :target: https://github.com/adamboche/marshmallow-attrs/compare/v0.1.1...master

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


Automatic generation of
`marshmallow <https://marshmallow.readthedocs.io/>`_ schemas from
dataclasses.

This package is based on
`marshmallow-dataclass <https://github.com/lovasoa/marshmallow_dataclass>`_.

Specifying a schema to which your data should conform is very useful,
both for (de)serialization and for documentation. However, using schemas
in python often means having both a class to represent your data and a
class to represent its schema, which means duplicated code that could
fall out of sync. With the new features of python 3.6, types can be
defined for class members, and that allows libraries like this one to
generate schemas automatically.

An use case would be to document APIs (with
`flasgger <https://github.com/rochacbruno/flasgger>`_, for
instance) in a way that allows you to statically check that the code
matches the documentation.


Installation
============

::

    pip install marshmallow-attrs

Documentation
=============


https://marshmallow-attrs.readthedocs.io/



Usage
=====

You simply import
```marshmallow_attrs.dataclass``
instead of `attr.dataclass <http://attrs.org>`_. It adds a
``Schema`` property to the generated class, containing a marshmallow
`Schema <https://marshmallow.readthedocs.io/en/2.x-line/api_reference.html#marshmallow.Schema>`_
class.

If you need to specify custom properties on your marshmallow fields
(such as ``attribute``, ``error``, ``validate``, ``required``,
``dump_only``, ``error_messages``, ``description`` ...) you can add them
using the ``metadata`` argument of the
`attr.ib <http://www.attrs.org/en/stable/api.html#attr.ib>`_
function.

.. code:: python

    import attr
    from marshmallow_attrs import dataclass # Importing from marshmallow_attrs instead of attrs
    import marshmallow.validate
    from typing import List, Optional

    @dataclass
    class Building:
      # The field metadata is used to instantiate the marshmallow field
      height: float = attr.ib(metadata={'validate': marshmallow.validate.Range(min=0)})
      name: str = attr.ib(default="anonymous")


    @dataclass
    class City:
      name: Optional[str]
      buildings: List[Building] = attr.ib(factory=lambda: [])

    # City.Schema contains a marshmallow schema class
    city, _ = City.Schema().load({
        "name": "Paris",
        "buildings": [
            {"name": "Eiffel Tower", "height":324}
        ]
    })

    # Serializing city as a json string
    city_json, _ = City.Schema().dumps(city)

The previous syntax is very convenient, as the only change you have to
apply to your existing code is update the ``dataclass`` import.

However, as the ``.Schema`` property is added dynamically, it can
confuse type checkers. If you want to avoid that, you can also use the
standard ``attr.s`` decorator, and generate the schema manually using
``class_schema``
:

.. code:: python

    import attr


    from datetime import datetime
    import marshmallow_attrs

    @attr.dataclass
    class Person:
        name: str
        birth: datetime

    PersonSchema = marshmallow_attrs.class_schema(Person)

You can also declare the schema as a
`ClassVar <https://docs.python.org/3/library/typing.html#typing.ClassVar>`_:

.. code:: python

    from marshmallow_attrs import dataclass
    from marshmallow import Schema
    from typing import ClassVar, Type

    @dataclass
    class Point:
      x:float
      y:float
      Schema: ClassVar[Type[Schema]] = Schema

You can specify the
`Meta <https://marshmallow.readthedocs.io/en/3.0/api_reference.html#marshmallow.Schema.Meta>`_
just as you would in a marshmallow Schema:

.. code:: python

    from marshmallow_attrs import dataclass

    @dataclass
    class Point:
      x:float
      y:float
      class Meta:
        ordered = True

Installation
------------

This package `is hosted on
pypi <https://pypi.org/project/marshmallow-attrs/>`_ :

.. code:: shell

    pip install marshmallow-attrs

Documentation
-------------

The project documentation is hosted on
`readthedocs <https://marshmallow-attrs.readthedocs.org>`_.

Usage warning
-------------

This library depends on python's standard
`typing <https://docs.python.org/3/library/typing.html>`_ library,
which is
`provisional <https://docs.python.org/3/glossary.html#term-provisional-api>`_.

Credits
-------

This package is based on
`marshmallow-dataclass <https://github.com/lovasoa/marshmallow_dataclass>`_.

.. |Build Status| image:: https://travis-ci.org/adamboche/marshmallow-attrs.svg?branch=master
   :target: https://travis-ci.org/adamboche/marshmallow-attrs
.. |PyPI version| image:: https://badge.fury.io/py/marshmallow-attrs.svg
   :target: https://badge.fury.io/py/marshmallow-attrs
