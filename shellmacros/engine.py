'''
This is the macro engine, it does the work of resolving macros
and managing your list of macros and their values.
'''
import os
import json
import re

from .entry import MacroEntry
from .result import MacroResult
from .exceptions import MacroSyntaxError, MacroUndefinedError, MacroRecursionError, MacroNonAsciiError
from .istr import IStr

FORMAT_MAJOR = 1
FORMAT_MINOR = 0
# This regex matches the first NON matching value
# \x0a = ASCII NEWLINE, ie: \n
# \x20 = ASCII SPACE
# \x7F = ASCII delete, we don't want that
# Thus (0x0a) + range(0x20 to 0x7e) is good
# the ^ at start means NOT
_non_ascii_regex = re.compile(r'[^\n -~]')

def _normalize_slash( s, slash_f, slash_t ):
    # internal not plublic function
    # normalizes dos/unix slashes

    # normalize
    s = s.replace( slash_f, slash_t )
    # what is the \\servername\path double slash?
    ss = slash_t + slash_t
    # do we have a DOS UNC filename?
    if s.startswith( ss ):
        # we do... special case
        tmp = ss
        s = s[2:]
    else:
        tmp = ''
    # Rebuild the string with the UNIX prefix if required
    # and replace all // with /
    tmp = tmp + s.replace( ss, slash_t )
    return tmp


def _make_quoted( s ):
    # s is a value for a make var
    # if this needs to be quoted, we need to fix it now
    need=False
    for ch in [ ' ', '\t', '"', "''"]:
        need = need or (ch in s)
    if not need:
        return s
    s = s.replace('"',r'\"')
    s = s.replace("'",r"\'")
    return '"' + s + '"'

def _bash_quoted(s):
    # same as makefile
    return _make_quoted(s)



class MacroEngine(object):
    '''
    This represents the macro engine.
    '''

    RESOLVE_NORMAL = 0
    RESOLVE_FULLY = 1
    RESOLVE_REFERENCES = 2

    def __init__(self):
        self.macros = dict()
        '''The macros, key: macro name, item=MacroEntry()'''
        self.use_env = False
        '''Should SHELL env variables be auto imported?'''
        self.ascii_check = True
        '''Should result strings be verified they are 100% pure ascii text?'''

    def add(self, name, value):
        '''Add a standard macro, ie: name = value, returns the added macro'''
        m = MacroEntry(name, value)
        self.macros[name] = m
        return m

    def add_makefle_dynamic_vars(self):
        '''Add makefile symbolic macros as KEEP & EXTERNAL'''
        for txt in "@%<?^+|*?":
            m = MacroEntry( 'x', None )
            m.name = txt
            m.keep = True
            m.external = True
            self.macros[txt] = m

    def add_external(self, name, value=None):
        '''Add an externally defined macro, returns the added macro.
        For example this might be your $PATH variable
        '''
        m = self.add(name, value)
        self.mark_macro_external(m.name)
        return m

    def disable_ascii_check(self):
        '''Disable accii output checks'''
        self.ascii_check = False

    def add_environment(self):
        '''Enable use of ENV variables'''
        self.use_env = True

    def add_keep(self, name, value):
        '''Add a macro that should not normally be expanded, returns the added macro'''
        m = self.add(name, value)
        self.mark_macro_keep(name)
        return m

    def mark_macro_keep(self, name):
        '''
        Mark this macro as a "keep" macro
        '''
        self.macros[name].keep = True

    def mark_macro_external(self, name):
        '''
        Mark this macro as some thing that is externally defined.
        '''
        self.macros[name].external = True

    def resolve_text(self, text, how=RESOLVE_NORMAL):
        '''Given text - resolve macros found in this text.

        If how == RESOLVE_NORMAL, then macros marked as external or how are not expanded.
        If how == RESOLVE_FULLY, then all macros marked as external or keep are fully expanded
        if how == RESOLVE_REFERENCES, then macros are are resolved fully and undefines are ignored

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
        result = MacroResult(text)

        # Loop till done
        while not result.done:
            # NOTE: Runaway recursion is handled
            #       in the 'result.update' operation
            self._resolve_pass(result, how)

        return result

    def _find_macro(self, name):
        # Internal function
        # find this macro
        # handle finding _dos/unix/_lc/_uc varients
        for passnum in (1, 2):
            # passnum = 1, original name
            # passnum = 2, handle uc/lc/dos/unix
            m = self.macros.get(name, None)
            if m:
                # found
                return m
            if self.use_env:
                e = os.getenv(name, None)
                if e:
                    # found, invent a macro so we know about it
                    m = MacroEntry(name, e)
                    # mark as an env macro
                    self.macrs[ name ] = m
                    m.env = True
                return m
            if passnum == 2:
                continue
            # between pass 1 & 2, we remove the suffixes
            if (name[-3:] in ('_uc', '_lc')):
                name = name[:-3]
            elif name.endswith('_dos'):
                name = name[:-4]
            elif name.endswith('_unix'):
                name =name[:-5]
            continue
        return None

    def _resolve_pass(self, result, how):
        # internal function
        # This makes one pass across the text, replacing 1 macro

        mresult = result.next_macro()
        if mresult.code == mresult.SYNTAX:
            result.declare_syntax()
            return

        if mresult.code == mresult.NOTFOUND:
            # We are done
            result.declare_success()
            return

        # We have something to remove/relace
        m = self._find_macro(mresult.name)
        if m is None:
            result.declare_undefined(mresult.name, False)
            return

        result.references.append(m)
        # what are we going to do?
        # REPLACE text or
        # MARK text?

        # Assume we will mark
        action_mark = False
        if how == self.RESOLVE_NORMAL:
            if (m.keep or m.external):
                action_mark = True
            else:
                action_mark = False
        elif how == self.RESOLVE_FULLY:
            action_mark = False
        elif how == self.RESOLVE_REFERENCES:
            if m.external and (m.value is None):
                action_mark = True
            else:
                action_mark = False

        if action_mark:
            result.mark(mresult.lhs, mresult.rhs, result.IGNORE)
            return

        value = m.value
        if value is None:
            result.declare_novalue(mresult.name)
            return

        # We are going to replace
        if m.quoted:
            value = '"%s"' % value

        if m.name != mresult.name:
            if mresult.name.endswith('_lc'):
                value = str.lower(value)
            elif mresult.name.endswith('_uc'):
                value = str.upper(value)
            elif mresult.name.endswith('_dos'):
                value = _normalize_slash( value, '/', '\\' )
            elif mresult.name.endswith('_unix'):
                value = _normalize_slash( value, '/', '\\' )
            else:
                raise NotImplementedError("What is this: %s != %s" % (m.name,mresult.name))
        result.replace(mresult.lhs, mresult.rhs, value)
        return

    def get(self, name, default=None):
        '''
        Treat the macros as a dictionary and GET/FIND an entry.

        :param name: The name to find
        :param default:  what to return if not found
        :return:  The macro entry, or None
        '''
        return self.macros.get(name, default)

    def output_order(self):
        '''Generates an suggested output order for variables

        Consider this sequence of bash variables:

        A=${B}
        B=foobar

        In a BASH script, variable A will be blank because B is not known yet.
        Thus, for BASH scripts it is better to reverse the order.

        This function calculates the correct order

        :return: List of macro names in dependency order
        '''
        result = []
        # clear all references
        for name, m in self.macros.items():
            m.references = []

        # Calculate all references
        for name, m in self.macros.items():
            # if this macro has no value or is externaly defined...
            if (m.value is None) or m.external or m.env:
                # consider the macro already present
                result.append(name)
                continue
            r = self.resolve_text(m.value, self.RESOLVE_REFERENCES)
            m.references = r.references[:]
        # Ok each macro now has a list of what it depends upon

        # Now, create our result
        forward_progress = True
        while True:
            # are we done? If so stop
            if len(result) == len(self.macros):
                break;

            # Get the list of names we need to
            # Because MACROS is a DICT... the key order is quasi-random
            # Thus, we sort the list of keys so that we evaulate things
            # in fixed order and unit tests don't have to worry about
            # quasi-random dict order
            todo = sorted(self.macros.keys())

            if not forward_progress:
                # Problem, we did not make forward progress
                raise MacroRecursionError('recursion involving macros: %s' % ' '.join(todo))

            # Assume no progress
            forward_progress = False
            while len(todo):
                # take one ...
                name = todo.pop()
                # if it is done already ...
                if name in result:
                    # Already did this one
                    continue

                # Assume this one is ok
                ok = True
                m = self.macros[name]
                # for each macro this macro references
                for r in reversed(m.references):
                    # if this is not yet in the list
                    if r.name not in result:
                        ok = False
                # was this one found?
                if not ok:
                    # nope, try another name
                    continue
                # Great we found one we are making progress
                forward_progress = True
                result.append(name)
        # when done give our completed list.
        return result

    def output_array(self):
        '''Returns Macros as ordered array of dict, that describes each macro

        Each entry in the array is dict that describes what should be outputed

        If 'd.output=False', then there is no meaningful output for this element.
        Generally is used to indicate a comment helpful to a human debugging scripts

        If d.output=true, then there is something to output, see: d.type for more details.

        The important items are:  d.name  The name of the macro, and d.value the value of the macro
        For MAKE and BASH scripts, sometimes a different equalsign might be required.
        For example a Makefile might use:  DATE := `date` instead of DATE=`date`
        or a makfile might use:  FOO ?= BAR instead of FOO = BAR

        '''
        aresult = []
        order = self.output_order()
        d = {
            'type': 'comment',
            'output': False,
            'comment': 'Generated by ShellMacros.py',
            'name': 'comment',
            'value': 'comment',
            'eq_bash': '=',
            'eq_make': '='
        }
        # insert our Generated macro here
        aresult.append(d)
        # NOTE:
        #   if the data here changes...
        #   YOU MUST CHANGE the FORMAT_MAJOR and FORMAT_MINOR
        # if you are adding more stuff, bump FORMAT_MINOR
        # if you are changing things entirely, bump FORMAT_MAJOR and reset FORMAT_MINOR
        assert( FORMAT_MAJOR == 1 )
        assert( FORMAT_MINOR == 0 )
        for name in order:
            m = self.macros[name]
            type = None
            value = m.value
            output = False
            comment = ''
            if m.env:
                type = 'env'
                value = 'Unknown'
            if m.external:
                type = 'ext'
                value = 'Unknown'
            if (type is None) and (value is None):
                type = 'novalue'
                value = 'Unknown'
            if type is None:
                type = 'normal'
                output = True
                r = self.resolve_text(value)
                if not r.ok:
                    raise r.error
                if r.result != value:
                    comment = 'orig: %s=%s' % (m.name, m.value)
                value = r.result
            d = {
                'type': type,
                'output': output,
                'comment': comment,
                'name': name,
                'value': value,
                'eq_make': m.eq_make,
                'eq_bash': m.eq_bash}
            aresult.append(d)
        return aresult

    def bash_fragment_arr(self):
        '''Return the macros as a BASH friendly array of strings'''
        aresult = self.output_array()
        result = [
            '#',
            '# Generated by ShellMacros.py',
            '#'
        ]
        for d in aresult:
            result.append('#')
            result.append('# type: %s' % d['type'])
            if len(d['comment']):
                result.append('# ' + d['comment'])
            if d['output']:
                result.append('%s%s%s' % (d['name'], d['eq_bash'], _bash_quoted(d['value'])))
            else:
                result.append('# no-output: %s = %s ' % (d['name'], d['value']))
        return result

    def bash_fragment_str(self):
        '''Return a string form of bash_fragment_arr()'''
        return self._ascii_sanity_check('\n'.join(self.bash_fragment_arr()))

    def make_fragment_arr(self):
        '''Return the macros as a GNU makefile friendly array of strings

        Nothing here that I know if is GNU makefile specific
        It should just work with other Unix makefiles... Your Milage May Very
        '''
        aresult = self.output_array()
        result = [
            '#',
            '# Generated by ShellMacros.py',
            '#'
        ]
        for d in aresult:
            result.append('#')
            result.append('# type: %s' % d['type'])
            if len(d['comment']):
                result.append('# ' + d['comment'])
            if d['output']:
                result.append('%s%s%s' % (d['name'], d['eq_make'], _make_quoted(d['value'])))
            else:
                result.append('# no-output: %s = %s' % (d['name'], d['value']))
        return result

    def make_fragment_str(self):
        '''returns a string form of make_fragment_arr()'''
        return self._ascii_sanity_check('\n'.join(self.make_fragment_arr()))

    def json_macros_str(self):
        '''Return the macros as a JSON string'''
        aresult = self.output_array()
        # NOTE: Human readablity in scripts is the reason we choose indent=4
        # Also, while technically this is an array...
        # we make it an object so that the JSON starts/ends with {} not []
        obj = { 'major' : FORMAT_MAJOR, 'minor' : FORMAT_MINOR, 'macros': aresult}
        jstr = json.JSONEncoder(indent=4, sort_keys=True).encode(obj)
        return self._ascii_sanity_check(jstr)

    def _ascii_sanity_check(self, s):
        # Generally build scripts are ASCII only, not unicode
        # This helps verify that the generated output is pure ascii
        if not self.ascii_check:
            return s
        # This: https://stackoverflow.com/questions/196345/how-to-check-if-a-string-in-python-is-in-ascii
        # talks about effiency, etc ...  We want a bit more of a restriction.
        # specifically we want:  (0x20 to 0x7e) - printable ascii
        # outside the printable range we only accept newline.
        # the ASCII test, allows for other bytes we do not want to support
        m = _non_ascii_regex.match(s)
        # most likely case
        if m is None:
            return s
        # something is wrong!
        for (lineno, line) in enumerate(s.split('\n')):
            m = _non_ascii_regex.match(s)
            if m is not None:
                raise MacroNonAsciiError('non-ascii in output, line: %d, text=%s' % (lineno + 1, line))
