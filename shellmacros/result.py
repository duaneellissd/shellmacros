'''
This represents a macro or text result.

Given some input, ie: "hello world" or  "some ${macro} text"

Resolve the text the MacroResult() is the result of that resolution.

'''

from .exceptions import *
from .istr import IStr

__all__ = ['MacroResult']

MAX_RECURSION = 50

class MacroResult(object):
    '''
    Base result type
    '''
    IGNORE = IStr.IGNORE

    def __init__(self, text_in):
        self.done = ('$' not in text_in)
        '''Is this result complete/done'''
        self.ok = self.done
        '''If done, is this result good/ok?'''
        self.history = [text_in]
        '''What happened during the translations'''
        self.istr = IStr( text_in )
        '''This is the work in process string'''
        self.error = None
        '''If an error occurs, this holds an Exception to throw'''
        self.keep = None
        '''Points to the first macro found that is marked as a EXTERNAL macro'''
        self.references = []
        '''List of macros that where used to resolve this string
        See MacroEngine.resolve_text() for details
        '''
        self.undefined = []
        '''When resolving for references, these undefined macros where found
        See MacroEngine.resolve_text() for details
        '''

    @property
    def result(self):
        '''The result of the macro resolution as a string'''
        if self.ok:
            return str(self.istr)
        else:
            return None

    def next_macro(self):
        '''Find the next macro'''
        return self.istr.next_macro(0,len(self.istr))

    def update_history(self, text):
        '''
        Append to the translation history
        '''
        if len(self.history) < MAX_RECURSION:
            self.history.append(text)
            return
        # overflow
        self.declare_recursion()

    def replace(self,lhs,rhs,value):
        '''Replace text between LHS and RHS with some value'''
        self.istr.replace(lhs,rhs,value)
        self.update_history( str(self.istr) )

    def mark(self,lhs,rhs,flagvalue=IGNORE):
        '''Mark this region as ignored or some other flag'''
        self.istr.mark( lhs,rhs,flagvalue)

        
    def declare_syntax(self):
        '''Declare a syntax error, we cannot go further'''
        self.ok = False
        self.done = True
        self.error = MacroSyntaxError("syntax: %s -> %s" % (self.history[0], self.history[-1]))

    def declare_recursion(self):
        '''Delcare a recursion error'''
        self.ok = False
        self.done = True
        self.error = MacroRecursionError("Recursion start: %s, now: %s" % (self.history[0], str(self.istr)))

    def declare_undefined(self,name, isext):
        '''Declare an undefined variable, we cannot go further'''
        self.ok = False
        self.done = True
        s = "undefined: %s -> %s undefined: %s" % (self.history[0], self.history[-1], name)
        if isext:
            s = "external-" + s
        self.error = MacroUndefinedError(s)

    def declare_success(self):
        '''Declare success, we are done'''
        self.ok = True
        self.done = True


