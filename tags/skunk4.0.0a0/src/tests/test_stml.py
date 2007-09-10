import cStringIO
import logging
import os
import unittest
import random
import tempfile

import webob

import skunk.stml as S
import skunk.components as C
from skunk.config import Configuration
from skunk.userlogger import getUserLogger

class SignatureTest(unittest.TestCase):

    def testArgs01(self):
        sig=S.Signature(())
        self.assertRaises(S.SignatureError,
                          sig.resolve_arguments,
                          ('foo',),
                          {})

    def testArgs02(self):
        sig=S.Signature(())
        res=sig.resolve_arguments((), {})
        self.assertEqual(res, {})

    def testArgs03(self):
        sig=S.Signature(('foo',))
        self.assertRaises(S.SignatureError,
                          sig.resolve_arguments,
                          ('boo', 'goo'),
                          {})

    def testArgs04(self):
        sig=S.Signature(('foo',))
        self.assertRaises(S.SignatureError,
                          sig.resolve_arguments,
                          ('boo',),
                          {'foo' : 4})

    def testArgs05(self):
        sig=S.Signature(('foo',))
        self.assertEquals({'foo' : 3},
                          sig.resolve_arguments((3,), {}))

    def testArgs06(self):
        sig=S.Signature(('foo',))
        self.assertEquals({'foo' : 3},
                          sig.resolve_arguments((),
                                                {'foo' : 3}))

    def testArgs07(self):
        sig=S.Signature(('foo', ('boo', 'HoHo!')))
        self.assertEquals({'foo' : 5, 'boo' : 'HoHo!'},
                          sig.resolve_arguments((5,), {}))

    def testArgs08(self):
        sig=S.Signature(('foo', ('boo', 'HoHo!')))
        self.assertRaises(S.SignatureError,
                          sig.resolve_arguments,
                          (4, 5, 6),
                          {})

    def testArgs09(self):
        sig=S.Signature(('foo', ('boo', 'HoHo!')))
        self.assertEquals({'foo' : 5, 'boo' : 'gong!'},
                          sig.resolve_arguments((5, 'gong!'), {}))        


    def testArgs10(self):
        sig=S.Signature(('foo', ('boo', 'HoHo!')))
        self.assertEquals({'foo' : 5, 'boo' : 'gong!'},
                          sig.resolve_arguments((5,),
                                                {'boo' : 'gong!'}))

    def testArgs11(self):
        sig=S.Signature(('name', 'value'))
        self.assertEquals({'name' : 'x', 'value' : None},
                          sig.resolve_arguments(('x', None), {}))

def _findfile(fname):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'files/%s' % fname)

def _prep_string(s):
    return '\n'.join(filter(None, [x.strip() for x in s.strip().split('\n')]))


_stml1=_prep_string("""
<:*

This is a comment that will be excluded from the lexer.
Putting another "<:*" here shouldn't make a difference.

*:>

<:args zoo=`1` foo garbanzo=ted "gogogo":>
<:z`s`:><:z`s`   :>
This is text.
<:j:>
""")


_stml2=_prep_string("""
<:set foo `3`:>
<:val `foo`:>
<:call `foo-=1`:>
<:val `foo`:>
<:for `range(foo)` x:>
<:val `10+x`:>
<:/for:>
""")

        
class LexTest(unittest.TestCase):
    def testLex1(self):
        res=S.dump_tokens(_stml1)
        l=len([x for x in res if isinstance(x, S.STMLToken) \
               and x.tokenType==S.t_START_TAG])
        self.assertEquals(l, 4, 'unexpected number of start tags')

    def assertTokenType(self, tokenType, token):
        self.assert_(isinstance(token, S.STMLToken), "expected STMLToken instance, got %s" % token)
        self.assert_(token.tokenType==tokenType, "expected %s, got: %s with text: %s" % (tokenType, token.tokenType, token.text))
                
    def testLex2(self):
        g=S.lex(_stml2)
        expected=[S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_TAGWORD,
                  S.t_EXPR, 
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_EXPR,
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_EXPR,
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_EXPR,
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_EXPR,
                  S.t_TAGWORD,
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_EXPR,
                  S.t_END_TAG,
                  S.t_TEXT,
                  S.t_START_TAG,
                  S.t_TAGNAME,
                  S.t_END_TAG,
                  ]

        for e in expected:
            self.assertTokenType(e, g.next())
        self.assertRaises(StopIteration, g.next)

                             
class ParseTest(unittest.TestCase):
    
    def testParse01(self):
        node=S.RootNode(globalTagDict=S.BaseTags)
        node.parse(S.lex("<:set x y:>"))
        self.assert_(len(node.children)==1)
        k=node.children[0]
        self.assert_(k.tagName=='set', "expected tagName 'set', got: %s" % k.tagName)
        self.failUnless(k.args==['x', 'y'], "unexpected args: %s" % str(k.args))
        self.failUnless(k._parsed_args=={'name' : 'x', 'value' : 'y'},
                        "unexpected _parsed_args: %s" % str(k._parsed_args))

    def testParse02(self):
        node=S.RootNode(globalTagDict=S.BaseTags)
        node.parse(S.lex("Pooh, ahoy!\n<:set x y:>\n"))
        self.assert_(len(node.children)==3, "expected 3 children, got: %d" % len(node.children))
        k=node.children[1]
        self.assert_(k.tagName=='set', "expected tagName 'set', got: %s" % k.tagName)
        self.failUnless(k.args==['x', 'y'], "unexpected args: %s" % str(k.args))
        self.failUnless(k._parsed_args=={'name' : 'x', 'value' : 'y'},
                        "unexpected _parsed_args: %s" % str(k._parsed_args))        

    def testParse03(self):
        node=S.RootNode(globalTagDict=S.BaseTags)
        self.assertRaises(S.ParseError,
                          node.parse,
                          S.lex(_stml1))

    def testParse04(self):
        node=S.RootNode(globalTagDict=S.BaseTags)
        node.parse(S.lex(_stml2))
        k=[x for x in node.children if isinstance(x, S.parser.Node)]
        self.failUnless(len(k)==5, "expected 5 children, got: %d" % len(k))

    def testParseCall01(self):
        node=S.CallTag()
        expr="x+=3"
        s="<:call `%s`:>" % expr
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'call')
        node.parse(g)
        self.assertEquals(len(node.args), 1)
        self.assertEquals(node.args[0].text, expr )
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        self.assertEquals(c.getvalue().strip(),
                          expr)

    def testParseSet01(self):
        node=S.SetTag()
        name="angst"
        value="pooh"
        s='<:set %s %s:>' % (name, value)
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'set')
        node.parse(g)
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        self.assertEquals(c.getvalue().strip(), "angst=('pooh')")

    def testParseVal01(self):
        node=S.ValTag()
        expr="4"
        s='<:val `%s`:>' % expr
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'val')
        node.parse(g)
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        self.assertEquals(c.getvalue().strip(), "__h.stml.write_val(4, OUTPUT, None)")

    def testParseVal02(self):
        node=S.ValTag()
        expr="4"
        s='<:val `%s` html:>' % expr
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'val')
        node.parse(g)
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        self.assertEquals(c.getvalue().strip(), "__h.stml.write_val(4, OUTPUT, 'html')")

    def testParseVal03(self):
        node=S.ValTag()
        expr='"this is a quoted string"'
        s='<:val %s:>' % expr
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'val')
        node.parse(g)
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        self.assertEquals(c.getvalue().strip(), "__h.stml.write_val('this is a quoted string', OUTPUT, None)")

    def testParseFor01(self):
        node=S.ForTag()
        expr='range(3)'
        name='x'
        s="<:for `%s` %s:>.<:else:>+<:/for:>" % (expr, name)
        g=S.lex(s)
        self.assertEquals(g.next().tokenType, S.t_START_TAG)
        self.assertEquals(g.next().text, 'for')
        node.parse(g)
        c=S.PythonCodeOutputStream()
        node.genCode(c)
        output=c.getvalue()
        expected="for %s in %s:\n    pass\n    OUTPUT.write('.')\nelse:\n    pass\n    OUTPUT.write('+')\n" % (name, expr)
        self.assertEquals(output, expected)


class CompTest(unittest.TestCase):
    def setUp(self):
        fd, self.fname=tempfile.mkstemp(suffix=".comp")
        self.f=os.fdopen(fd, 'w')

    def tearDown(self):
        os.unlink(self.fname)

    def testSpacing1(self):
        for i in range(10):
            if i % 2:
                self.f.write('%d\n' % i)
            else:
                self.f.write('\n')
            
        self.f.write('FIN\n')
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res, open(self.fname).read())
        
    def testComp01(self):
        self.f.write("<:for `range(x)`:>\n  <:val x:>\n<:/for:>\n\n")
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        
        x=random.randrange(200)
        res=c({'x' : x})
        self.assertEquals(res, "\n%s\n" % ('  x\n\n' * x))
        self.assertEquals(x, res.count('x'))

    def testComp02(self):
        self.f.write("""<:spool tmp:>
        <:for `range(x)` n:>
           Loop no. <:val `n`:>
        <:/for:>
        <:/spool:>
        <:val `tmp`:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(200)
        res=c({'x': x})
        self.assertEquals(x, res.count('Loop'))


    def testComp03(self):
        self.f.write("""
        <:default MAX `100`:>
        <:for `range(x)` n:>
          <:if `n>=MAX`:>
            <:break:>
          <:else:>
            POOH
          <:/if:>
        <:/for:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(500)
        res=c({'x': x})
        self.assertEquals(min(x, 100), res.count('POOH'))
        res=c({'x': x, 'MAX' : 20})
        self.assertEquals(min(x, 20), res.count('POOH'))


    def testComp04(self):
        self.f.write("""
        <:default MAX `100`:>
        <:for `range(x)` n:>
          <:if `n>=MAX`:>
            <:raise `ReturnValue`:>
          <:else:>
            POOH
          <:/if:>
        <:/for:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(500)
        res=c({'x': x})
        self.assertEquals(min(x, 100), res.count('POOH'))
        res=c({'x': x, 'MAX' : 20})
        self.assertEquals(min(x, 20), res.count('POOH'))


    def testComp05(self):
        self.f.write("""
        <:import re:>
        <:set pat `re.compile('hi')`:>
        <:spool tmp:>
           <:for `range(x)` n:>
              hi, Mussolini!
           <:/for:>
        <:/spool:>
        <:val `pat.sub('Bye', tmp)`:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(200)
        res=c({'x': x})
        self.assertEquals(x, res.count('Bye'))

    def testComp06(self):
        self.f.write("""
        <:try:>
           <:call `foo`:>
        <:except `NameError`:>
           <:set foo `20`:>
        <:else:>
           GONG
        <:/try:>
        <:val `foo`:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(100)
        res=c({'foo' : x})
        self.assertEquals(res.count('GONG'), 1)
        self.assertEquals(res.count('%s' % x), 1)
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res.count('GONG'), 0)
        self.assertEquals(res.count('20'), 1)


    def testComp07(self):
        self.f.write("""
        <:default x `20`:>
        <:while `x>0`:>
          <:if `x % 2`:>
             odd
          <:else:>
             even
          <:/if:>
         <:call `x-=1`:>
       <:else:>
           Nothing here, go home
       <:/while:>
       """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res.count('odd'), 10)
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        x=random.randrange(40)
        res=c({'x' : x})
        self.assertEquals(res.count('odd'), (x/2) + (x % 2))


    def testComp08(self):
        self.f.write("""
        <:comment:>
        In this  test, I'm going to try
        nesting stuff in a comment tag
        to verify that it isn't called:

        <:default x `500`:>

        <:/comment:>

        <:#:>

        I'll also use a brief comment, which should be equivalent.
        <:/#:>

        <:* and also use the kind of comment
        that you can put any stuff in, like <:z:>
        and <:foo:> and <:/goober:>.
        *:>
        <:default x "ahoy there":>
        <:val `type(x)`:>
        <:val `x`:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res.count("ahoy there"), 1)


    def testComp09(self):
        self.f.write("""
        <:filter:>
        hello there
        <:/filter:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res.count('hello there'), 1)

        
    def testComp10(self):
        self.f.write("""
        <:filter filter=xml:>
        5 < 10
        <:/filter:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.assertEquals(res.strip(), "5 &lt; 10")


    def testComp11(self):
        self.f.write("""
        <:filter boo:>
        <<<
        <:filter filter=xml:>
        <<<
        <:/filter:>
        <:/filter:>
        <:val `boo`:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.failUnless(res.count('<<<'), 1)
        self.failUnless(res.count('&lt;&lt;&lt;'), 1)

    def testComp12(self):
        self.f.write("""
        <:import re sub:>
        <:val `sub('foo', 'boo', "Say 'foo'")`:>
        <:del sub:>
        <:try:>
           <:val `sub`:>
        <:except `NameError`:>
           YES
        <:/try:>
        """)
        self.f.close()
        c=S.STMLFileComponent(self.fname,
                              tagVocabulary=S.BaseTags)
        res=c()
        self.failUnless(res.count('boo'), 1)
        self.failUnless(res.count('YES'), 1)

    def testComp13(self):
        self.f.write("Hello from me!\n")
        self.f.close()
        fd, fname=tempfile.mkstemp(suffix=".comp")
        try:
            f=os.fdopen(fd, 'w')
            f.write("""
            I'm going to call a component now.
            <:component `compname`:>
            Done.
            """)
            f.close()
            suffixes=C.DEFAULT_FILE_COMPONENT_SUFFIX_MAP.copy()
            suffixes['.comp']=('string', S.STMLFileComponent)
            Configuration.load_dict(dict(componentFileSuffixMap=suffixes))
            res=C.stringcomp(fname, compname=self.fname)
            print res
            self.failUnless('Hello from me!\n' in res)
        finally:
            os.unlink(fname)
        
    def testComp14(self):

        fd, fname=tempfile.mkstemp(suffix=".inc")
        try:
            f=os.fdopen(fd, 'w')
            f.write("""
            Hello from me!
            <:set x `33`:>
            """)
            f.close()        
            self.f.write("""
            I'm going to call a component now.
            <:include `compname`:>
            x is <:val `x`:>.
            Done.
            """)
            self.f.close()
            suffixes=C.DEFAULT_FILE_COMPONENT_SUFFIX_MAP.copy()
            suffixes['.comp']=('string', S.STMLFileComponent)
            suffixes['.inc']=('include', S.STMLFileComponent)
            Configuration.load_dict(dict(componentFileSuffixMap=suffixes))        
            res=C.stringcomp(self.fname, compname=fname)
            print res
            self.failUnless('Hello from me!\n' in res)
            self.failUnless("x is 33" in res)
        finally:
            os.unlink(fname)

    def testComp15(self):
        fd, fname=tempfile.mkstemp(suffix=".inc")
        dfd, dfname=tempfile.mkstemp(suffix='.pydcmp')
        try:
            f=os.fdopen(fd, 'w')
            df=os.fdopen(dfd, 'w')
            f.write("""
            Hello from me!
            <:datacomp x  `dcompname`:>
            """)
            f.close()
            df.write("raise ReturnValue, 33\n")
            df.close()
            self.f.write("""
            I'm going to call a component now.
            <:include `compname`:>
            x is <:val `x`:>.
            Done.
            """)
            self.f.close()
            res=C.stringcomp(self.fname, compname=fname, dcompname=dfname)

            self.failUnless('Hello from me!\n' in res)
            self.failUnless("x is 33" in res)
        finally:
            os.unlink(fname)
            os.unlink(dfname)
            
    def testPre01(self):
        self.f.write("""<:?pre off?:>
<:call `
def foo(x):
    return x + 100
`:>
<:val `foo(100)`:>
""")

        self.f.close()
        res=C.stringcomp(self.fname)
        self.failUnless(res=='200')

    def testPre02(self):
        self.f.write("<:?pre off?:>\n\n\n\nhi\n\n\n")
        self.f.close()
        res=C.stringcomp(self.fname)
        self.failUnless(res=='hi')

    def testLog1(self):
        self.f.write('hi there <:debug "about to compile the borkoscape":>')
        self.f.close()
        logger=getUserLogger()
        logger.setLevel(logging.DEBUG)
        sio=cStringIO.StringIO()
        logger.addHandler(logging.StreamHandler(sio))
        res=C.stringcomp(self.fname)
        self.failUnless('hi there' in res)
        v=sio.getvalue()
        self.failUnless('borkoscape' in v)

    def testLog2(self):
        self.f.write('hi there <:info "ding dong %s" `4`:>')
        self.f.close()
        logger=getUserLogger()
        logger.setLevel(logging.DEBUG)
        sio=cStringIO.StringIO()
        logger.addHandler(logging.StreamHandler(sio))
        res=C.stringcomp(self.fname)
        self.failUnless('hi there' in res)
        v=sio.getvalue()
        self.failUnless('ding dong 4' in v)

    def testLog3(self):
        self.f.write('hi there <:try:><:raise `ValueError`:><:except:><:exception "ding dong %s" `4`:><:/try:>')
        self.f.close()
        logger=getUserLogger()
        logger.setLevel(logging.DEBUG)
        sio=cStringIO.StringIO()
        logger.addHandler(logging.StreamHandler(sio))
        res=C.stringcomp(self.fname)
        self.failUnless('hi there' in res)
        v=sio.getvalue()
        print v
        self.failUnless('ding dong 4' in v)
        
    def testArgsTag1(self):
        self.f.write("<:args x=`int` y z=`(int,12)`:>\n")
        self.f.write("x: <:val `str(x)`:>\n")
        self.f.write("y: <:val `str(y)`:>\n")
        self.f.write("z: <:val `z+0`:>\n")
        self.f.close()
        request=webob.Request.blank('/foo')
        res=C.stringcomp(self.fname, REQUEST=request)
        print res
        self.failUnless('x: None' in res)
        self.failUnless('y: None' in res)
        self.failUnless('z: 12' in res)
        
if __name__=='__main__':
    unittest.main()


