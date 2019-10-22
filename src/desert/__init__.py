import desert._make


def schema(cls, many=False):
    """Build a schema for the class.
    """
    return desert._make.class_schema(cls)(many=many)


def schema_class(cls):
    """Build a schema class for the class.



    """
    return desert._make.class_schema(cls)
