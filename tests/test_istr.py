import sys

sys.path.insert(0,"..")
import unittest

import shellmacros

class TestISTR( unittest.TestCase ):
    def test_ONE( self ):
        shellmacros.istr.test_istr

if __name__ == '__main__':
    unittest.main()
