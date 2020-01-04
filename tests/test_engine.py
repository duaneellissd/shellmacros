from unittest import TestCase

import shellmacros


class TestMacroEngine(TestCase):
    def setup1(self):
        e = shellmacros.MacroEngine()
        e.add('zack_dog', 'dolly')
        e.add('what','${pet}')
        e.add('pet','dog')
        e.add('parent', 'duane')
        e.add('duane_son', 'zack')
        e.add_keep('keep','_keep_me')
        e.add_external('extern')
        e.add('EXTERN','${extern}')
        return e

    def test_A010_simple(self):
        e = self.setup1()
        r = e.resolve_text('')
        self.assertTrue(r.ok)
        self.assertEqual(r.result , '' )

    def test_A020_simple(self):
        e = self.setup1()
        r = e.resolve_text('${parent}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result,'duane')

    def test_A030_simple(self):
        e = self.setup1()
        r=e.resolve_text( '${${${parent}_son}_${what}}' )
        assert(r.ok)
        self.assertEqual(r.result,'dolly')

    def test_B010_ext(self):
        def permutation( rr, ee, kk, full ):
            e = self.setup1()
            if ee:
                e.mark_macro_external(ee)
            if kk:
                e.mark_macro_keep(kk)
            r = e.resolve_text('${zack_dog}',full)
            self.assertTrue( r.ok )
            if( r.result != rr ):
                # here so we can set a breakpoint
                self.assertEqual( r.result , rr )
        permutation( 'dolly', None, None, False )
        permutation( 'dolly', None, None, True )
        permutation( '${zack_dog}', 'zack_dog', None, False )
        permutation( 'dolly'      , 'zack_dog', None, True )
        permutation( '${zack_dog}', None      , 'zack_dog', False )
        permutation( 'dolly'      , None      , 'zack_dog', True  )

    def test_B020_find_a_keep(self):
        e = self.setup1()
        e.mark_macro_keep('zack_dog')
        r = e.resolve_text('${${${parent}_son}_${what}}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result,'${zack_dog}')
        # test that we can resolve this
        r = e.resolve_text('${${${parent}_son}_${what}}',True)
        self.assertTrue(r.ok)
        self.assertEqual(r.result,'dolly')

    def test_B030_expand_an_extern(self):
        e = self.setup1()
        e.mark_macro_keep('duane_son')
        r = e.resolve_text('${${${parent}_son}_${what}}',True)
        self.assertTrue(r.ok)
        self.assertEqual(r.result, 'dolly')
        r = e.resolve_text('${${${parent}_son}_${what}}', False)
        self.assertFalse( r.ok)
        self.assertIsNone (r.result)

    def test_C010_extern(self):
        e =self.setup1()
        r = e.resolve_text('abc ${EXTERN} xyz',False)
        self.assertTrue(r.ok)
        self.assertEqual( r.result , 'abc ${extern} xyz' )

    def test_C020_transfors(self):
        e = shellmacros.MacroEngine()
        input=r'//Server\MixedCase'
        e.add( 'a', input )

        # no change
        r = e.resolve_text('${a}')
        self.assertTrue(r.ok)
        self.assertEqual( r.result, input )

        # lower
        r = e.resolve_text('${a_lc}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result, input.lower())

        # upper
        r = e.resolve_text('${a_uc}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result, input.upper())

        # DOS
        r = e.resolve_text('${a_dos}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result, input.replace('/','\\'))

        # Unix
        r = e.resolve_text('${a_unix}')
        self.assertTrue(r.ok)
        self.assertEqual(r.result, input.replace('/', '\\'))

    def test_NEG_010_syntax(self):
        e = self.setup1()

        s = '${noclose'
        r = e.resolve_text(s)
        self.assertTrue(r.ok)
        self.assertEqual( r.result, s)

        s = 'noopen}'
        r = e.resolve_text(s)
        self.assertTrue(r.ok)
        self.assertEqual(r.result, s)

        e.add('A', '${B}')
        e.add('B', '${A}')
        r = e.resolve_text('${A}')
        self.assertFalse( r.ok )
        self.assertIsInstance(r.error,shellmacros.MacroRecursionError)

    def order_test_setup(self):
        e = shellmacros.MacroEngine()
        # goal:  ${${abc}} -> ${${a}_{b}_{c}}
        #        a=a, b=dogs, c=lunch
        #        ${a_dogs_lunch} => is_not_tasty
        e.add('a', 'a')
        e.add('b', 'dogs')
        e.add('c', 'lunch')
        e.add('abc', '${a}_${b}_${c}')
        e.add('a_dogs_lunch', 'is_not_tasty')
        e.add('foo', '${${abc}}')
        return e
    def test_E010_depends(self):
        e = self.order_test_setup()
        r = e.resolve_text( '${foo}', e.RESOLVE_REFERENCES )
        r = e.output_order()
        correct = ['c', 'b', 'a_dogs_lunch', 'a', 'abc', 'foo']
        self.assertEqual( len(r) , len(correct) )
        for x in range(0,len(r)):
            self.assertEqual( correct[x] , r[x] )
        # Done.
    def test_E020_make(self):
        e = self.order_test_setup()
        j = e.json_macros_str()
        # this is not easy to test..  so we eyeball it
        print('JSON result:\n---------\n%s\n---------' % j)
        print("")
    def test_E030_bash(self):
        e = self.order_test_setup()
        b = e.bash_fragment_str()
        # this is not easy so we eyeball it
        print('BASH result:\n---------\n%s\n---------' % b)
        print("")

    def test_E040_bash(self):
        e = self.order_test_setup()
        m = e.make_fragment_str()
        # this is not easy so we eyeball it
        print('MAKE result:\n---------\n%s\n---------' % m)
        print("")

    def test_E050_quoted_keeps(self):
        e = shellmacros.MacroEngine()
        e.add_keep( "CC", "${CROSS_COMPILE}gcc" )
        e.add_keep( "CROSS_COMPILE", "arm-none-eabi-")
        e.add_external("WORKSPACE_LOC")
        m=e.add("SOMEDIR", r"C:\path with\spaces in\path")
        m.quoted = True
        e.add_makefle_dynamic_vars()
        e.add( "cmd", "${CC} -o I${WORKSPACE_LOC}/foo -I${SOMEDIR} -o ${@} ${<}" )
        s=e.make_fragment_str()
        print("MAKE RESULT\n-----\n%s\n------\n" % s)
        s=e.bash_fragment_str()
        print("BASH RESULT\n-----\n%s\n------\n" % s )
        print("")
