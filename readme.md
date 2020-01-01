# Shell Macro Helper

This is a macro engine that helps manage SHELL and MAKEFILE like macros.

## Background
Typically a macro has both a `name` and a `value`.

But - if you are creating packages for use in embedded systems you often need something more
and you find that you need to use macros, and need to resolve them "in-situ" that complicates things.

Thus this package is aimed at people writing library like modules that pubilsh configuration files
and/or other small fragment files like: Make fragments, or Bash Script fragments.

## How it helps

To help solve and address this, macros have more then just the `name = value` pair, they have:

* `name` - the name of the macro (Restriction, it must be a valid C language variable name)
* `value` - This might be unknown, or it might be known
* `keep` - A flag that indicates the macro should sometimes be kept and not expanded.
* `external` - A flag that indicates this variable variable is a 'keep' variable and its value is externally defined

# Examples

Here are some examples, the `CROSS_COMPILE` macro from the Linux Kernel

```
# CROSS_COMPILE might be:  "arm-none-eabi-"
AS		= $(CROSS_COMPILE)as
LD		= $(CROSS_COMPILE)ld
CC		= $(CROSS_COMPILE)gcc
CPP		= $(CC) -E
# ... others not shown for breivity reasons

# PROJECT_LOC is a dynamic variable created by Eclipse
# and resolves to the directory where the ".project" file is located.
LIBCONFIG_DIR=${PROJECT_LOC}/../libconfig_dir
```

You might expect the user to define `CROSS_COMPILE` or you might provide a default value as an example.

But what you do not want is all of the uses of `${CROSS_COMPILE}` to be expanded. You might want other macros expanded but not `${CROSS_COMPILE}`

Hence you would mark `CROSS_COMPILE` as a "keep"

You also might not ever know the value of `${PROJECT_LOC}` Eventually - later it will be known but not now.

Hence you would mark `PROJECT_LOC` as an external.

Here's how you would use this:

```
import shellmacros

engine = shellmacros.MacroEngine()

engine.add_keep('CROSS_COMPILE', 'arm-none-eabi-')
engine.add_external( 'PROJECT_LOC' )

# fully expand everything
result = engine.resolve_text( "${CC} -c foo.c -o foo.o", True )
assert( result.ok )
# Go compile a file
os.system( result.result )

# Expand, but honor keep 
engine.add_external('*')
engine.add_external('@')
engine.add_keep("XYZZY", "-DPLUGH=1")
engine.add( "make_commnad", "${CC} -c ${*}.c -o ${@} ${XYZZY}")
result = engine.resolve_text( "${make_command}" )
# CC and XYZZY are expanded, but * and @ are not
```

Once you have done the above, you can then output fragments in useful ways

```
with open("frag.mk","w") as f:
    # note: Make does not care about the order of macros...
    f.write( engine.make_variables_string )

with open("frag.sh","w") as f:
    # BASH requires an order, otherwise macros don't expand correctly
    f.write( engine.bash_variables_string )

with open("frag.json", "w") as f:
    # JSON does not care, its just data not really variables.
    f.write( engine.json_text )
```


