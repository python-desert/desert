..
   TODO: figure out proper location for this stuff including making it public
         if in desert


desert._fields module
=====================

Tagged Unions
-------------

Serializing and deserializing data of uncertain type can be tricky.
Cases where the type is hinted with :class:`typing.Union` create such cases.
Some solutions have a list of possible types and use the first one that works.
This can be used in some cases where the data for different types is sufficiently unique as to only work with a single type.
In more general cases you have difficulties where data of one type ends up getting processed by another type that is similar, but not the same.

In an effort to reduce the heuristics involved in serialization and deserialization an explicit tag can be added to identify the type.
That is the basic feature of this group of utilities related to tagged unions.

A tag indicating the object's type can be applied in various ways.
Presently three forms are implemented: adjacently tagged, internally tagged, and externally tagged.
Adjacently tagged is the most explicit form and is the recommended default.
You can write your own helper functions to implement your own tagging form if needed and still make use of the rest of the mechanisms implemented here.

- A class definition and bare serialized object for reference

    .. code-block:: python

        @dataclasses.dataclass
        class Cat:
            name: str
            color: str

    .. code-block:: json

        {
            "name": "Max",
            "color": "tuxedo",
        }

- Adjacently tagged

   ..  include:: ../snippets/tag_forms/adjacent.rst

- Internally tagged

   ..  include:: ../snippets/tag_forms/internal.rst

- Externally tagged

   ..  include:: ../snippets/tag_forms/external.rst

The code below is an actual test from the Desert test suite that provides an example usage of the tools that will be covered in detail below.

.. literalinclude:: ../../tests/test_fields.py
   :start-after: # start tagged_union_example
   :end-before: # end tagged_union_example


Fields
......

A :class:`marshmallow.fields.Field` is needed to describe the serialization.
This role is filled by :class:`desert._fields.TaggedUnionField`.
Several helpers at different levels are included to generate field instances that support each of the tagging schemes shown above.
:ref:`Registries <tagged_union_registries>` are used to collect and hold the information needed to make the choices the field needs.
The helpers below create :class:`desert._fields.TaggedUnionField` instances that are backed by the passed registry.

.. autofunction:: desert._fields.adjacently_tagged_union_from_registry
.. autofunction:: desert._fields.internally_tagged_union_from_registry
.. autofunction:: desert._fields.externally_tagged_union_from_registry

.. autoclass:: desert._fields.TaggedUnionField
   :members:
   :undoc-members:
   :show-inheritance:


.. _tagged_union_registries:

Registries
..........

Since unions are inherently about handling multiple types, fields that handle unions must be able to make decisions about multiple types.
Registries are not required to leverage other pieces of union support if you are developing their logic yourself.
If you are using the builtin mechanisms then a registry will be needed to define the relationships between tags, fields, and object types.

..
   TODO: sure seems like the user shouldn't need to call Nested() themselves

The registry's :meth:`desert._fields.FieldRegistryProtocol.register` method will primarily be used.
As an example, you might register a custom class ``Cat`` by providing a hint of ``Cat``, a tag of ``"cat"``, and a field such as ``marshmallow.fields.Nested(desert.schema(Cat))``.

.. autoclass:: desert._fields.FieldRegistryProtocol
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: desert._fields.TypeAndHintFieldRegistry
   :members:
   :undoc-members:
   :show-inheritance:
