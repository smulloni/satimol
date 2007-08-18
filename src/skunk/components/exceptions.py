class ComponentHandlingException(Exception):
    pass

class ComponentArgumentError(ValueError):
    pass

class ReturnValue(Exception):
    """
    An exception class for sending return values out of data components.
    """
    def value(self):
        if self.args:
            return self.args[0]
    value=property(value, None, None, None)
