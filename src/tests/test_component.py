import unittest
import os
import random
import tempfile
import shutil

from skunk.components import *

someCode="""\
raise ReturnValue, a*(x**y)
"""

class BasicComponentTest(unittest.TestCase):
    def setUp(self):
        self.comp1=Component(code=someCode, name='testcomponent')
        self.tmpdir=tempfile.mkdtemp()
        self.comp2=Component(code=someCode,
                             compileCache=CompileCache(self.tmpdir),
                             name='testcomponent')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        
    def testCallNoCompileCache(self):
        comp=self.comp1
        d={'a' : 3,
           'x' : 2,
           'y' : 5}
        value=comp(d)
        assert value==(3*(2**5))

    def testCallWithCompileCache(self):
         comp=self.comp2
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
               name=COMPONENT.name
               comp=COMPONENT.factory.createComponent(name)
               print >> OUTPUT, comp({'m' : m/2,
                                      'c' : c/2})
        
        print >> OUTPUT, '###################'
        """
        # undo the indent
        i=s.index('f')
        s='\n'.join([x[i:] for x in s.split('\n')])
        self.f.write(s)
        self.f.close()
        factory=ComponentFactory({'file' : LocalFileComponentHandler()})
        comp=factory.createComponent(self.fname)
        #comp=StringOutputFileComponent(self.fname)
        res=comp()
        self.assertEquals(comp.componentStack, [])
        
class FactoryTest(unittest.TestCase):
    def setUp(self):
        handlers={'file' : LocalFileComponentHandler(),
                  'callable' : CallableComponentHandler()}
        self.factory=ComponentFactory(handlers)
        fd, self.fname=tempfile.mkstemp(suffix=".pycomp")
        self.f=os.fdopen(fd, 'w')

    def tearDown(self):
        os.unlink(self.fname)
        
    def test01(self):
        self.f.write("print >> OUTPUT, 'Hello World'\n")
        self.f.close()
        comp=self.factory.createComponent(self.fname)
        res=comp()
        self.assertEquals(res, "Hello World\n")
        
                   
if __name__=='__main__':
    unittest.main()
