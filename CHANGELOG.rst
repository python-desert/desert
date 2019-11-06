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
