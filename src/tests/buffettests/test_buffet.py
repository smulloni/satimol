import os

from skunk.stml import BuffetPlugin
from skunk.web import template, TEMPLATING_ENGINES


def test_stml():
    pass

if 'breve' in TEMPLATING_ENGINES:
    def test_breve():
        here=os.path.dirname(os.path.abspath(__file__))
        @template('breve:%s/brevetest' % here,
                  format='html')
        def tester():
            return dict(message="my message",
                        mytitle="my title")
        res=tester()
        assert "my message" in res
        assert "my title" in res

if 'mako' in TEMPLATING_ENGINES:
    def test_mako():
        pass

if 'genshi' in TEMPLATING_ENGINES:
    def test_genshi():
        @template('genshi:tests.buffettests.genshitest', format='html')
        def tester():
            return dict(message='my message',
                        mytitle='my title')
        res=tester()
        assert "my message" in res
        assert "my title" in res


        
