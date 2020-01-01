'''
Created on Dec 27, 2019

@author: duane

'''

DOLLAR = ord('$')
LBRACE = ord('{')
RBRACE = ord('}')
LPAREN  = ord('(')
RPAREN  = ord(')')


class IStr(list):
    '''
    This closely models a basic ASCII string
    Note: Unicode strings are expressly not supported here.

    The problem this addresses occurs during macro processing.
    Sometimes macros are defined externally

    Other times, macros are fully defined with a package.

    Often macros need to be resolved either partially or fully

    When a macro is only external - they get in the way of resolving other macros
    To work around that, we convert the string into an array of integers

    Then for every macro byte that is 'external' we add 0x100 
    This makes the byte 'non-matchable'

    Later, when we convert the resolved string into we strip the 0x100.
    '''

    IGNORE = 0x100

    def __init__(self, s):
        '''
        Constructor
        '''
        # convert to integers
        list.__init__(self, map(ord, s))

    def __str__(self):
        # return as string, stripping flags
        return ''.join(map(lambda v: chr(v & 0xff), self))

    def sslice(self, lhs, rhs):
        # return as string, stripping flags
        return ''.join(map(lambda v: chr(v & 0xff), self[lhs:rhs]))

    def iarray(self):
        return self[:]

    def mark(self, lhs, rhs, flagvalue=IGNORE):
        '''
        Apply flags to locations between left and right hand sides, ie: [lhs:rhs]
        '''
        for idx in range(lhs, rhs):
            self[idx] |= flagvalue

    def locate(self, needle, lhs, rhs):
        '''Find this needle(char) in the hay stack(list).'''
        try:
            return self.index(needle, lhs, rhs)
        except:
            # not found
            return -1

    def replace(self, lhs, rhs, newcontent):
        '''replace the data between [lhs:rhs] with newcontent'''
        self[lhs: rhs] = map(ord, newcontent)

    def next_macro(self, lhs, rhs):
        '''
        Find a macro within the string, return (lhs,rhs) if found
        If not found, return (-1,-1)
        If syntax error, return (-2,-2)
        '''

        rhs = self.locate(RBRACE, lhs,rhs)
        if rhs >= 0:
            _open_symbol = LBRACE
        else:
            rhs = self.locate(RPAREN,lhs,rhs)
            _open_symbol = LPAREN

        if rhs < 0:
            # not found
            return (-1, -1, None)

        lhs = -1
        while lhs < rhs:
            # find our DOLLAR
            lhs = self.locate(DOLLAR, lhs + 1, rhs)
            if lhs < 0:
                # a stray RBRACE syntax error
                return (-2, -2, None)

            # Look for $ then {, we have } already
            ch = self[lhs + 1]
            if ch != _open_symbol:
                # stray dollar, we ignore
                continue

                # Do we have a nested macro, ie: ${${x}}
            tmp = self.locate(DOLLAR, lhs + 1, rhs)
            if tmp > 0:
                lhs = tmp - 1
                continue
            # nope, we are good
            return (lhs, rhs + 1, self.sslice(lhs + 2, rhs))
        # not found syntax stray  dollar or brace
        return (-2, -2, None)


def test_istr():
    def check2(l, r, text, dut):
        print("----")
        print("Check (%d,%d)" % (l, r))
        print("s = %s" % str(dut))
        print("i = %s" % dut.iarray())
        (lt, rt, text) = dut.next_macro(0, len(dut))
        if (lt != l) or (rt != r):
            print("str = %s" % str(dut))
            print("int = %s" % dut.iarray())
            print("Error: (%d,%d) != (%d,%d)" % (l, r, lt, rt))
            assert (False)
        dut.mark(l, r)
        return dut

    def check(l, r, s):
        if l >= 0:
            expected = s[l + 2:r - 1]
        else:
            expected = None
        dut = IStr(s)
        check2(l, r, expected, dut)
        st = str(dut)
        assert (st == s)
        return dut

    check(-1, -1, "")
    check(-1, -1, "a")
    check(-1, -1, "ab")
    check(-1, -1, "abc")
    check(-1, -1, "abcd")
    check(-1, -1, "abcde")
    check(-1, -1, "abcdef")

    check(0, 4, "${a}")
    check(0, 5, "${ab}")
    check(0, 6, "${abc}")
    check(0, 7, "${abcd}")

    check(1, 5, "a${a}")
    check(2, 6, "ab${a}")
    check(3, 7, "abc${a}")
    check(4, 8, "abcd${a}")
    check(5, 9, "abcde${a}")

    check(0, 4, "${a}a")
    check(0, 4, "${a}ab")
    check(0, 4, "${a}abc")
    check(0, 4, "${a}abcd")
    check(0, 4, "${a}abcde")

    dut = check(4, 8, "abcd${a}xyz")
    dut.replace(4, 8, "X")
    check2(-1, -1, None, dut)
    r = str(dut)
    print("Got: %s" % r)
    assert ("abcdXxyz" == str(dut))
    # now nested tests

    dut = check(5, 9, "abc${${Y}}xyz")
    dut.replace(5, 9, "X")
    r = str(dut)

    assert (r == "abc${X}xyz")
    dut = check2(3, 7, "${X}", dut)
    dut.replace(3, 7, "ABC")
    s = str(dut)
    r = "abcABCxyz"
    assert (s == r)
    print("Success")


if __name__ == '__main__':
    test_istr()
