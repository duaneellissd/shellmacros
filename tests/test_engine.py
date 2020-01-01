from unittest import TestCase

import shellmacros

class TestMacroEngine(TestCase):
    def step1(self):
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
        e = self.step1()
        r = e.resolve_text("")
        assert(r.ok)
        assert(r.result == "" )
        assert(r.keep is None)
        assert(r.external is None)

    def test_A020_simple(self):
        e = self.step1()
        r = e.resolve_text("${parent}")
        assert(r.ok)
        assert(r.result=='duane')
        assert(r.external is None)
        assert(r.keep is None)

    def test_A030_simple(self):
        e = self.step1()
        r=e.resolve_text( '${${${parent}_son}_${what}}' )
        assert(r.ok)
        assert(r.result=='dolly')
        assert(r.keep is None)
        assert(r.external is None)

    def test_B010_ext(self):
        def permutation( rr, ee, kk, full ):
            e = self.step1()
            if ee:
                e.mark_macro_external(ee)
            if kk:
                e.mark_macro_keep(kk)
            r = e.resolve_text("${zack_dog}",full)
            assert( r.ok )
            if( r.result != rr ):
                # here so we can set a breakpoint
                assert( r.result == rr )
            if ee:
                assert( r.external.name == ee )
            else:
                assert( r.external == None )
            if kk:
                assert( r.keep.name == kk )
            else:
                assert( r.keep == None )
        permutation( 'dolly', None, None, False )
        permutation( 'dolly', None, None, True )
        permutation( '${zack_dog}', 'zack_dog', None, False )
        permutation( 'dolly'      , 'zack_dog', None, True )
        permutation( '${zack_dog}', None      , 'zack_dog', False )
        permutation( 'dolly'      , None      , 'zack_dog', True  )

    def test_B020_find_a_keep(self):
        e = self.step1()
        e.mark_macro_keep('zack_dog')
        r = e.resolve_text('${${${parent}_son}_${what}}')
        assert(r.ok)
        assert(r.result=='${zack_dog}')
        assert(r.keep.name == 'zack_dog')
        assert(r.external is None)
        # test that we can resolve this
        r = e.resolve_text('${${${parent}_son}_${what}}',True)
        assert(r.ok)
        assert(r.result=='dolly')
        assert(r.keep.name == 'zack_dog')
        assert(r.external is None)

    def test_B030_expand_an_extern(self):
        e = self.step1()
        e.mark_macro_keep('duane_son')
        r = e.resolve_text('${${${parent}_son}_${what}}',True)
        assert(r.ok)
        assert(r.result =='dolly')
        assert(r.keep.name=='duane_son')
        assert(r.external is None)
        r = e.resolve_text('${${${parent}_son}_${what}}', False)
        assert ( not r.ok)
        assert (r.result is None)
        assert (r.keep.name == 'duane_son')
        assert (r.external is None)

    def test_C010_extern(self):
        e =self.step1()
        r = e.resolve_text("abc ${EXTERN} xyz",False)
        assert(r.ok)
        self.assertEqual( r.result , "abc ${extern} xyz" )
        assert(r.external.name == 'extern')
        assert(r.keep is None)



