
__all__ = [ 'MacroRecursion', 'MacroUndefined','MacroSyntax','MacroBadName']

class MacroRecursion(Exception):
    pass

class MacroUndefined(Exception):
    pass

class MacroSyntax(Exception):
    pass

class MacroBadName(Exception):
    pass