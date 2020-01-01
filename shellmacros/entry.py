import re

__all__ = [ 'MacroEntry' ]


from .exceptions import MacroBadName

# C sytle variable name 
#   <letter_or_under><letter|digits|under>...
valid_name = re.compile( r'[A-Za-z_][A-Z0-9]*')

class MacroEntry( object ):
    '''
    This represents one macro entry, a name and value
    
    A macro may also be marked as external, meaning it is externally defined
    For example your ENV variable $PATH might be externally defined.
    
    A macro may also be marked as keep, meaning it should remain as a macro.
    A keep macro is not expanded unless it is requested to do so.
    
    For example, when creating a Makefile or Shell script component
    You might have a "base" macro for example ${FOO_DIR}
    
    The a series of other macros that use ${FOO_BAR} as reference.
    A good Makefile example might be:  ${CC} = ${CROSS_COMPILE}gcc
    And the variable ${CPP} (the c-pre-processor)
    
    The output should contain 3 variables: CROSS_COMPILE=arm-eabi-none-
    
    Expanded, CC=arm-eabi-none-gcc, but we want CC=${CROSS_COMPILE}gcc
    
    The macro may be marked as "keep" meaning the macro should not be expanded
    Or may be marked as externally defined
    '''
    
    def __init__( self, name, value= None ):
        self._filename = None
        self._lineno = None

        self.name = name
        '''The name of this macro, for example FOO=BAR, the value FOO'''

        # Names must be reasonable and conform to C langauge variable specification
        if None == valid_name.match( name ):
            raise MacroBadName("bad-macro-name: %s" % name )

        self.value = value
        '''The value of this macro. Note value can be None
       
        The Eclipse IDE provides many dynamic variables such as ${ECLIPSE_HOME}
        or ${PROJECT_LOC} which will at some future time be known
        
        But for now, the variable could be None.
        '''
        self.external = False
        '''This macro might not exist until a future time
        
        An example is the Eclipse dynamic variable: ${PROJECT_LOC} we do not know
        While right now we might know the current location of the project
        The value of this macro will change if things "move" so we treat
        this macro as a special case.
        '''
        self.keep = False
        '''This macro is known, but we generally do not want to expand unless required.
        
        For example, when creating a Makefile, we might want "CC=${CROSS_COMPILE}gcc"
        
        In this case, we might know that "${CROSS_COMIPILE}=arm-none-eabi-" but
        sometimes we want to fully expand ${CC} and other times we do not
        
        for example we might want the ${CROSS_COMPILE} macro to be expanded by Make later
        and thus, the ${CC} macro would also be expanded later
        '''

    def str_where(self):
        '''Return a string representing where the maro was defined'''
        return "%s:%d" % (self._filename,self._lineno)

    def remember_where(self, filename, lineno):
        '''Remember where this macro was defined'''
        self._filename = filename
        self._lineno = lineno


