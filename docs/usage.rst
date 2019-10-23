=======
Usage
=======

.. include:: ../README.rst
    :start-after: start-basic-usage
    :end-before: end-basic-usage


Use custom marshmallow fields like this.

.. testcode::

     import dataclasses
     import datetime

     import desert
     import marshmallow


     @dataclasses.dataclass
     class A:

         # Use `desert.ib()` instead for attrs.
         x: str = desert.field(marshmallow.fields.NaiveDateTime())

         y: int = dataclasses.field(metadata=desert.metadata(marshmallow.fields.Int()))

     timestring = "2019-10-21T10:25:00"
     dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
     schema = desert.schema(A)

     assert schema.load({"x": timestring, "y": 5}) == A(x=dt, y=5)

.. testoutput::
