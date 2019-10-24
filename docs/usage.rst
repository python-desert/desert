.. currentmodule:: desert

=======
Usage
=======

Basics
-------

.. include:: ../README.rst
    :start-after: start-basic-usage
    :end-before: end-basic-usage


Desert can be used with :mod:`dataclasses` or :mod:`attr`. With either module,
Desert is able to infer the appropriate :mod:`marshmallow` field
for any of these types:

* :class:`int`
* :class:`float`
* :class:`bool`
* :class:`str`
* :class:`datetime.datetime`
* :class:`datetime.time`
* :class:`datetime.timedelta`
* :class:`datetime.date`
* :class:`uuid.UUID`
* :class:`decimal.Decimal`
* :class:`enum.Enum`

If you have :mod:`marshmallow_union` installed, then :class:`typing.Union` is handled by
trying to deserialize into each of the unioned types until one succeeds.



There are two syntaxes for
specifying a field.

In the more concise form, :func:`desert.field()` wraps :mod:`dataclasses.field()` and
:func:`desert.ib()` wraps :func:`attr.ib()`. These functions take a
:class:`marshmallow.fields.Field` as the first argument, and the remaining arguments are
forwarded to the corresponding wrapped function.

In the more verbose form, simply use the normal functions :func:`dataclasses.field()` and
:func:`attr.ib()`, but provide the ``metadata`` value using :func:`desert.metadata()`,
which returns a dict of values namespaced for :mod:`desert` to use.

Use with :mod:`dataclasses`
-------------------------------

.. testcode::

     import dataclasses
     import datetime

     import desert
     import marshmallow


     @dataclasses.dataclass
     class Entry:

         timestamp: str = desert.field(marshmallow.fields.NaiveDateTime())

         # Or use the more verbose form.
         favorite_number: int = dataclasses.field(default=3, metadata=desert.metadata(field=marshmallow.fields.Int()))

     schema = desert.schema(Entry)

     print(schema.load({"timestamp": "2019-10-21T10:25:00", "favorite_number": 42}))

.. testoutput::

    Entry(timestamp=datetime.datetime(2019, 10, 21, 10, 25), favorite_number=42)


Use with :mod:`attrs`
---------------------------


.. testcode::

     import datetime

     import attr
     import desert
     import marshmallow


     @attr.dataclass
     class Entry:

         timestamp: str = desert.ib(marshmallow.fields.NaiveDateTime())

         # Or use the more verbose form.
         favorite_number: int = attr.ib(default=3, metadata=desert.metadata(field=marshmallow.fields.Int()))

     schema = desert.schema(Entry)

     print(schema.load({"timestamp": "2019-10-21T10:25:00", "favorite_number": 42}))


.. testoutput::

    Entry(timestamp=datetime.datetime(2019, 10, 21, 10, 25), favorite_number=42)



Testing :mod:`marshmallow` and :mod:`attr` and :mod:`attrs`.
