'''
This is the macro engine, it does the work of resolving macros
and managing your list of macros and their values.
'''

from .entry import MacroEntry
from .result import MacroResult
from .exceptions import MacroSyntax, MacroUndefined, MacroRecursion


class MacroEngine(object):
    '''
    This represents the macro engine.
    '''
    def __init__(self):
        self.macros = dict()
        
    def add( self, name, value ):
        '''Add a standard macro, ie: name = value, returns the added macro'''
        m = MacroEntry( name, value )
        self.macros[ name ] = m
        return m
        
    def add_external(self, name, value = None):
        '''Add an externally defined macro, returns the added macro.
        For example this might be your $PATH variable
        '''
        m = self.add( name,value)
        self.mark_macro_external(m.name)
        return m

    def add_keep(self,name,value):
        '''Add a macro that should not normally be expanded, returns the added macro'''
        m = self.add(name,value)
        self.mark_macro_keep(name)
        return m

    def mark_macro_keep(self, name):
        '''
        Mark this macro as some thing we want to not expand.
        '''
        self.macros[name].keep = True
        
    def mark_macro_external(self,name):
        '''
        Mark this macro as some thing that is externally defined.
        '''
        self.macros[name].external = True

    def resolve_text(self, text, full = False ):
        '''
        Given text - resolve macros found in this text.
        If full = true, then we require a fully resolved macro
        If full = false, then external or keep macros will not be resolved.

        NOTE: In the most "unpythonic way" ...

        This specifically does not THROW syntax errors
        Nor does this THROW undefined errors

        Reason, the tool above (client of this module)- should examine the result.
        If the reslt is NOT ok, the tool most often will want to ADD more
        information to the error then raise the error.

        For example if the client is parsing a file, the client may want to
        add filename and line number to the error so that the user has a
        more pleasent experience with your tool.

        Consider these messages:

           error: undefined: FOO
        verses:
           somefilename.txt:134: error undefined: FOO
        '''
            
        # Get our result
        result = MacroResult( text )
        
        # Loop till done
        while not result.done:
            self._resolve_pass( result, full )
            
        return result


    def _resolve_pass(self, result, full ):
        '''
        This makes one pass across the text
        if we made changes, return true (ie: make another pass)
        if no changes, then return false, we are done.
        
        If full=True, then we require a fully resolved macro.
        We fail if we cannot resolve a macro.
        '''
        (lhs,rhs,name) = result.next_macro()
        if lhs == -2:
            result.declare_syntax()
            return

        if lhs == -1:
            # We are done
            result.declare_success()
            return
        
        # We have something to remove/relace
        m = self.get(name,None)
        if m is None:
            # TODO:
            #   Should support things like ${str.upper(${NAME})}
            #   The macro name where would be: str.upper(...)
            #   We could examine the string find the ()s
            #   and look up the string .. in this case it is str.upper
            #   We could then call the function: str.upper()
            #   Did this before ... it was very powerful
            result.declare_undefined(name,False)
            return

        if (m.external or m.keep):
            # caller specifies if they want it fully resolved or not
            pass
        else:
            # we require this to be fully resolved
            full = True
        # update the external/keep flags based on this macro
        if m.external:
            result.external = m
        if m.keep:
            result.keep = m

        if full:
            # we require a value
            if m.value is None:
                result.declare_undefined(name,m.external)
                return
        if not full:
            # we don't fully resolve
            result.mark( lhs,rhs, result.IGNORE )
        else:
            # replace
            result.replace( lhs, rhs, m.value )

    def get(self,name, default=None):
        '''
        Treat the macros as a dictionary and GET/FIND an entry.

        :param name: The name to find
        :param default:  what to return if not found
        :return:  The macro entry, or None
        '''
        return self.macros.get( name,default)

            