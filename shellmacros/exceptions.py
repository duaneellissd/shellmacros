
__all__ = [ 'MacroRecursionError', 'MacroUndefinedError','MacroSyntaxError','MacroBadNameError','MacroNonAsciiError']

class MacroRecursionError(Exception):
    pass

class MacroUndefinedError(Exception):
    pass

class MacroSyntaxError(Exception):
    pass

class MacroBadNameError(Exception):
    pass

class MacroNonAsciiError(Exception):
    pass

