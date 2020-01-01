from unittest import FunctionTestCase

import shellmacros

class TestIStr(FunctionTestCase):
    def __init__(self):
        foo = IStr('dog')
        FunctionTestCase.__init__(self, shellmacros.istr.test_istr)


