import desert._make


def schema(cls, many=False, **kw):
    """Build a schema for the class."""
    return desert._make.class_schema(cls, **kw)(many=many)


def schema_class(cls, **kw):
    """Build a schema class for the class."""
    return desert._make.class_schema(cls, **kw)
