''' A simple macro package that manages ${macros}

The aim of this Macro package is quite a bit more then simple ${name} replacement.
Specifically, the special features are known as: "keep" and "external"

Generally, a macro always has a NAME and a VALUE
Macros have 2 additional attributes:  "keep" and "external"

If a macro is external=True then the VALUE may be None as it is unknown.
Note that an external=True macro may optionally have a value but that is optional.

If a macro is keep=True, then the VALUE is required

What matters is during the engine.resolve_text(input,full=False) call.

The intent of this package is to help create reusable Makefile & BASH fragments
that maintian certian variables.

A good example is the common Makefile macro: CC=${CROSS_COMPILE}gcc

Often the variable: CROSS_COMPILE=arm-none-eabi-.
This would normally result in CC=arm-none-eabi-gcc

As tools process things, tools sometimes need to "fully" expand all macros
While other times, they want to keep ${CROSS_COMPILE} as a macro

Hence, the engine.resolve_text() has an optional "full=True" or "full=False" parameter

'''
from .engine import MacroEngine
from .istr import IStr
from .entry import MacroEntry
from .result import MacroResult
from .exceptions import *

