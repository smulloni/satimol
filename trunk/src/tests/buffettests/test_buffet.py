import logging
import os

from skunk.config import Configuration
from skunk.web import template, TEMPLATING_ENGINES

logging.basicConfig(level=logging.DEBUG)

here=os.path.dirname(os.path.abspath(__file__))

def test_stml():
    Configuration.load_kw(componentRoot=here)
    @template('stml:/stmltest.stml')
    def tester():
        return dict(message="my message",
                    mytitle="my title")
    res=tester()
    assert "my message" in res
    assert "my title" in res


if 'breve' in TEMPLATING_ENGINES:
    def test_breve():
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
        @template('mako:%s/makotest.html' % here, format='html', options=dict(directories=['/']))
        def tester():
            return dict(message='my message',
                        mytitle='my title')
        res=tester()
        assert "my message" in res
        assert "my title" in res


if 'genshi' in TEMPLATING_ENGINES:
    def test_genshi():
        @template('genshi:tests.buffettests.genshitest', format='html')
        def tester():
            return dict(message='my message',
                        mytitle='my title')
        res=tester()
        assert "my message" in res
        assert "my title" in res


        
