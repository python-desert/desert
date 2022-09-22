2022.09.22 (2022-09-22)
-----------------------


Backward-incompatible Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update all project dependencies and fix all deprecated warnings. Python 3.6
  support was dropped to allow updating deprecated dependencies.
  `#161 <https://github.com/python-desert/desert/issues/161>`_


Changes
^^^^^^^

- It is now possible to use `type-variant generics`_ in your dataclasses, such as ``Sequence``
  or ``MutableSequence`` instead of ``List``, ``Mapping`` instead of ``Dict``, etc.

  This allows you to hide implementation details from users of your dataclasses. If a field
  in your dataclass works just as fine with a tuple as a list, you no longer need to force
  your users to pass in a ``list`` just to satisfy type checkers.

  For example, by using ``Mapping`` or ``MutableMapping``, users can pass ``OrderedDict`` to
  a ``Dict`` attribute without MyPy complaining.

  .. code-block:: python

      @dataclass
      class OldWay:
          str_list: List[str]
          num_map: Dict[str, float]


      # MyPy will reject this even though Marshmallow works just fine. If you use
      # type-variant generics, MyPy will accept this code.
      instance = OldClass([], collections.ChainMap(MY_DEFAULTS))


      @dataclass
      class NewWay:
          str_list: List[str]  # Type-invariants still work
          num_map: MutableMapping[str, float]  # Now generics do too


  .. _type-variant generics: https://mypy.readthedocs.io/en/stable/generics.html
  `#140 <https://github.com/python-desert/desert/issues/140>`_


----


2020.11.18 (2020-11-18)
-----------------------


Changes
^^^^^^^

- Schemas no longer copy non-field dataclass attributes. Thanks to @sveinse for report and test.
  `#79 <https://github.com/python-desert/desert/issues/79>`_


----


2020.01.06 (2020-01-06)
-----------------------


Changes
^^^^^^^

- Additional metadata are supported in ib() and fields(). Thanks to @sveinse for reporting and testing.
  `#28 <https://github.com/python-desert/desert/issues/28>`_


----


2020.01.05 (2020-01-05)
-----------------------


Changes
^^^^^^^

- Add support for attrs factories that take ``self`` (``attr.Factory(..., takes_self=True)``).
  `#27 <https://github.com/python-desert/desert/issues/27>`_


----


2020.01.04 (2020-01-04)
-----------------------


Changes
^^^^^^^

- Add support for Tuple[int, ...] per https://docs.python.org/3/library/typing.html#typing.Tuple
  `#16 <https://github.com/python-desert/desert/issues/16>`_ Thanks to @sveinse for reporting and testing.
- Use module imports internally.
  `#18 <https://github.com/python-desert/desert/issues/18>`_
- Desert version only needs to be updated in _version.py
  `#19 <https://github.com/python-desert/desert/issues/19>`_
- Fix doctests.
  `#20 <https://github.com/python-desert/desert/issues/20>`_


----


2020.01.03
--------------

Changes
^^^^^^^^

- ``Optional`` fields allow ``None``. `#11 <https://github.com/python-desert/desert/issues/11>`__. Thanks to @sveinse for reporting and testing.

2019.12.18
--------------

Changes
^^^^^^^

- Improve error message for unknown generics.
  `#10 <https://github.com/python-desert/desert/pull/10>`_

2019.12.10
--------------

Changes
^^^^^^^

- Add ``UnknownType`` exception with better error message for types that should be generic.
  `#8  <https://github.com/python-desert/desert/issues/8>`_



2019.12.09
--------------

Changes
^^^^^^^

- Marshmallow schema ``Meta`` arguments are accepted, allowing exclusion of unknown fields and other options.
  `#3  <https://github.com/python-desert/desert/pull/3>`_

2019.11.06 (2019-11-06)
-----------------------


Changes
^^^^^^^

- Add twine and wheel development dependencies.
  `#2 <https://github.com/python-desert/desert/issues/2>`_


----


2019.11.06 (2019-11-06)
-----------------------

Changes
^^^^^^^

- Switch to calver


Backward-incompatible Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Non-optional fields without a default or factory now have `required=True` so raise :class:`marshmallow.exceptions.ValidationError` when missing.
  `#1 <https://github.com/python-desert/desert/issues/1>`_


----

0.1.0 (2019-06-22)
------------------

Changes
^^^^^^^

- First release on PyPI.

---
