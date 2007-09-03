import os
import skunk.config.scopes as SC


class TestScope(object):
    
    def setUp(self):
        self.sc=SC.ScopeManager()
        self.sc.setDefaults(pong='askew',
                            bolo='nightmarish')
    def tearDown(self):
        pass
        

    def test_scope1(self):
        self.sc.load_kw(bolo='happy-go-lucky')
        self.sc._matchers.append(SC.StrictMatcher('kong', 'donkey', bolo='hiatus'))
        assert self.sc.bolo=='happy-go-lucky'
        assert self.sc.pong=='askew'
        self.sc.scope(dict(kong='donkey'))
        assert self.sc.bolo=='hiatus'
        assert self.sc.pong=='askew'
        self.sc.trim()
        assert self.sc.bolo=='happy-go-lucky'
        assert self.sc.pong=='askew'
        self.sc.reset()
        assert self.sc.bolo=='nightmarish'
        assert self.sc.pong=='askew'

    def test_scope2(self):
        self.sc._matchers.append(SC.RegexMatcher('kong', '^Leo|Gertrude', pong='hiya'))
        self.sc.scope(dict(kong='Leo told her to buy new socks'))
        assert self.sc.pong=='hiya'


def test_file1():
    sc=SC.ScopeManager()
    sc.load(os.path.join(os.path.dirname(__file__), 'files/conftests/fc1.conf'))
    assert sc.kong=='Julie loves toast'
    sc.scope(dict(HTTP_HOST='www.tonka.org:80'))
    assert sc.kong=='pong'

def test_file2():
    sc=SC.ScopeManager()
    sc.load(os.path.join(os.path.dirname(__file__), 'files/conftests/fc2.conf'))
    assert sc.bum=='hog'

def test_file3():    
    sc=SC.ScopeManager()
    sc.load(os.path.join(os.path.dirname(__file__), 'files/conftests/fc2.conf'))
    assert sc.bum=='hog'
    sc.scope(dict(path='/images/hoo'))
    assert sc.bum=='image'
    sc.trim()
    sc.scope(dict(path='/images/hoo.jpg'))
    assert sc.bum=='jpeg'
    
