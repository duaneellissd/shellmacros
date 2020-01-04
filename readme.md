# Shell Macro Helper

This is a macro engine that helps manage SHELL and MAKEFILE like macros.

You create an engine and add macros follows

```
import shellmacros 

engine = shellmacros.MacroEngine()

# generic name
m1 = engine.add("FOO", "BAR")

# See below, about keep macros
m2 = engine.add_keep("CROSS_COMPILE", "arm-none-eabi-" )

# See below about Eclipse Macros
m3 = engine.add_ext( "WORKSPACE_LOC" )

# make system ENV variables available
engine.add_environment()

```

## Background
Generically a macro has both a `name` and a `value`.

* Restriction: Names must match a C Variable name, ie: Start with a letter ... etc.

Often though, you need more then Names and Values 

Sometimes you need to resolve the macro, other times you need the macro to remain so that it will
be evaluated and resolved "in-situ" in the final script.  Other times you need macros that are partially expandded

The goal of this package is to help with the above problems.

## How it helps

To help solve and address this, macros have more then just the `name = value` pair, they have:

* `name` - the name of the macro (Restriction, it must be a valid C language variable name)
* `value` - This might be unknown, or it might be known
* `keep` - A flag that indicates the macro should sometimes be kept and not expanded.
* `external` - A flag that indicates this variable variable is a 'keep' variable and its value is externally defined
* `eq_make` - When outputing a Make fragment, what type of equal sign should be used.
* `eq_bash` - When outputing a Bash fragment, what type of equal should be used.

### About Equal Signs

Makefile macros can be assigned in several forms (GNU Syntax)

* The most common: `NAME = VALUE` (this is the default)
* Changing:  `macro.eq_make = ':='`
* Results in:  `NAME := VALUE`
* Other values such as `?=` can be used

## Examples for KEEP, and EXTERNAL

Here are some examples, the `CROSS_COMPILE` macro from the Linux Kernel is a good example

```
# CROSS_COMPILE might be:  "arm-none-eabi-"
AS		= $(CROSS_COMPILE)as
LD		= $(CROSS_COMPILE)ld
CC		= $(CROSS_COMPILE)gcc
CPP		= $(CC) -E
# ... others not shown for breivity reasons

# PROJECT_LOC is a dynamic variable used by Eclipse scripts and makefiles
# and resolves to the directory where the ".project" file is located.
LIBCONFIG_DIR=${PROJECT_LOC}/../libconfig_dir
```

### Keep Macros

Your tool might output a default value for `CROSS_COMPILE` Howver, in your 
output you may or may not want all the `${CROSS_COMPILE}` items expanded. 
You might choose instead to mark CROSS_COMPILE as a KEEP 

You also might not ever know the value of `${PROJECT_LOC}` Eventually - later it will be 
known but not now. But other times you might need to use a temporary value for PROJECT_LOC for other reasons.

Hence you would mark `PROJECT_LOC` as an external, and may optionally give it a value

Here's how you would use this:

```
import shellmacros

engine = shellmacros.MacroEngine()

engine.add_keep('CROSS_COMPILE', 'arm-none-eabi-')
engine.add_external( 'PROJECT_LOC' )

# fully expand everything
result = engine.resolve_text( "${CC} -c foo.c -o foo.o", engine.RESOLVE_FULLY )
assert( result.ok )
# Go compile a file
os.system( result.result )
```

Makefile macro example
``` 
# Add macros for ${*}, ${@}, etc
engine.add_make_dynamic_vars()
engine.add_keep("XYZZY", "-DPLUGH=1")
engine.add( "make_commnad", "${CC} -c ${<} -o ${@} ${XYZZY}")
# provide values for these macros
m = engine.macros['<']
m.value = "foo.c"
m = engine.macros['@']
m.value = 'foo.o'
# do not expand ${@}
result_normal = engine.resolve_text( "${make_command}" )
# Fully expand all macros, including '@' and "*"
result_full   = engine.resolve_text( "${make_command}", engine.RESOLVE_FULLY )
```
# Simple helpful transforms

Some simplistic macro transforms are supported, for example:

```
# Given ...
engine.add( "FOOBAR", "Caps_And_Lower" )

# Auto upper/lower case this macro
# _lc suffix means the macro value in lower case.
all_lower = engine.resolve("${FOOBAR_lc}" )
# _uc is upper case
all_upper = engine.resolve("${FOOBAR_uc}" )

#  DOS/UNIX slashes are often a problem
# For example you may have mixed slashes
# And/or accidently have double \\ when not required
engine.add( "FOO", "src/foobar\\abc.c" )
# The _dos and _unix suffix normalizes paths
# The _dos suffix, transforms all slashes to DOS format
dos_path = engine.resolve("${FOO_dos}")
# The _unix suffix, transforms all slashes to UNIX format
unix_path = engine.resolve("${FOO_unix}")
```

# Hint - output additional macros

Adding macrosl like this makes it easier to write scripts
```
# Consider the macro FOO and NAME
# You might want the UC/LC and/or DOS/UNIX varients
# It's easy to make this happen

# Example path names
engine.add( "FOO", "src/foobar\\abc.c" )
engine.add( "FOO_dos", "${FOO_dos}" )
engine.add( "FOO_unix", "${FOO_unix}" }
# Example names
engine.add( "NAME", "Mixed_Case_Name" )
engine.add( "NAME_lc", "${NAME_lc}" )
engine.add( "NAME_uc", "${NAME_uc}" )
```

## Macro Output Order

The ultimate goal is to output macros for consumption by another tool.

Macro order matters. Consider these two macros in a BASH verses MAKE script
```
A=${B}
C=cat
B=${C}
```

If the script was a MAKEFILE, the above would just work because
Make evaluates macros when they are used, not when they are read

In contrast, BASH evaluates macros as they are read, when BASH evaluates
the assignment for A, variable B is not yet known - thus this fails.

The solution is `engine.output_order()` which returns an array/list of 
macro names such that the evaluation order is correct.

In the above, the correct order would be ['C', 'B', 'A']

## Outputing Macros

Option 1, is to write your own formatter using: `engine.output_array()`


```
with open("frag.mk","w") as f:
    # note: Make does not care about the order of macros...
    f.write( engine.make_fragment_str() )

with open("frag.sh","w") as f:
    # BASH requires an order, otherwise macros don't expand correctly
    f.write( engine.bash_fragment )

with open("frag.json", "w") as f:
    # JSON does not care, its just data not really variables.
    f.write( engine.json_vars )
```


