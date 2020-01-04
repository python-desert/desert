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
