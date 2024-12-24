class PynaristError(Exception):
    """
    Class for all Pynarist errors.
    """

    @classmethod
    def new(cls, *messages):
        result = cls()
        for msg in messages:
            result.add_note(str(msg))
        return result


class ParseError(PynaristError):
    """
    Error raised when parsing fails.
    """

    pass


class BuildError(PynaristError):
    """
    Error raised when building fails.
    """

    pass


class UsageError(PynaristError):
    """
    Error raised when method arguments are incorrect.
    """

    pass
