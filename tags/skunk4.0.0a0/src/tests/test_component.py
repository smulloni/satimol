import logging
import os
import random
import shutil
import sys
import tempfile
import unittest

logging.basicConfig(level=logging.DEBUG, file=sys.stderr)

from skunk.config import Configuration as Cfg
from skunk.components import *

someCode="""\
raise ReturnValue, a*(x**y)
"""

class BasicComponentTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir=tempfile.mkdtemp()
        Cfg.setDefaults(compileCacheRoot=self.tmpdir)
        self.comp1=Component(code=someCode, name='testcomponent')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        Cfg.reset()
        
    def testCallNoCompileCache(self):
        c=ComponentContext.compileCache
        ComponentContext.compileCache=None
        try:
            comp=self.comp1
            d={'a' : 3,
               'x' : 2,
               'y' : 5}
            value=comp(d)
            assert value==(3*(2**5))
        finally:
            ComponentContext.compileCache=c

    def testCallWithCompileCache(self):
        Cfg.load_dict(dict(useCompileMemoryCache=True))
        comp=self.comp1
        d={'a' : 3,
           'x' : 2,
           'y' : 5}
        value=comp(d)
        assert value==(3*(2**5))

class StringOutputFileComponentTest(unittest.TestCase):
    def setUp(self):
        f=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files/hello.pycomp')
        self.comp1=StringOutputFileComponent(f)
        
    def testCall(self):
        comp=self.comp1
        n=random.randint(1, 6)
        d={'iterations' : n}
        s=comp(d)
        assert s.count('hello')==n

class StackedComponentTest(unittest.TestCase):

    def setUp(self):
        fd, self.fname=tempfile.mkstemp(suffix=".pycomp")
        self.f=os.fdopen(fd, 'w')

    def tearDown(self):
        os.unlink(self.fname)

    def test01(self):
        s="""\
        from skunk.components import *
        import random
        try:
            m
        except NameError:
            m=100

        try:
            c
        except NameError:
            c=4
            
        if m < 10:
            raise ReturnValue

        hits=[random.randrange(m) for i in range(c)]

        print >> OUTPUT, '####################'
        for i in range(m):
           print >> OUTPUT, "iteration %d" % i
           if  i in hits:
               # get current component file
               name=ComponentContext.componentStack[-1].name
               print >> OUTPUT, stringcomp(name, m=m/2, c=c/2)
        
        print >> OUTPUT, '###################'
        """
        # undo the indent
        i=s.index('f')
        s='\n'.join([x[i:] for x in s.split('\n')])
        self.f.write(s)
        self.f.close()
        res=stringcomp(self.fname)
        self.assertEquals(ComponentContext.componentStack, [])
        
def test_componentRoot1():
    tmpdir=tempfile.mkdtemp()
    Cfg.load_kw(componentRoot=tmpdir)
    try:
        fname=os.path.join(tmpdir, 'index.stml')
        fp=open(fname, 'w')
        fp.write('\n'.join([
            "<:default kong Chubby:>",
            "Hello <:val `kong`:>"
            "<:component /nougat.comp cache=yes:>"
            ]))
        fp.close()
        fp=open(os.path.join(tmpdir, 'nougat.comp'), 'w')
        fp.write('SERVES YOU RIGHT')
        fp.close()
        res=stringcomp('/index.stml', kong='Kong')
        assert 'Hello Kong' in res
    finally:
        Cfg.reset()
        shutil.rmtree(tmpdir)
        
if __name__=='__main__':
    unittest.main()
