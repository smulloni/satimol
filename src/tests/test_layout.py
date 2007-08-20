import os
import shutil
import tempfile

from skunk.config import Configuration as Cfg
import skunk.components as C
import skunk.stml as S
from skunk.util.pathutil import translate_path


class TestLayout(object):

    def __init__(self):
        self.componentRoot=tempfile.mkdtemp()
        
    def setup(self):
        Cfg.load_kw(componentRoot=self.componentRoot)

    def tearDown(self):
        shutil.rmtree(self.componentRoot)
        Cfg.reset()
    
    def test_layout1(self):
        template='<:compargs SLOTS=`{}`:><:for `"first second third".split()` name:><:slot `name`:><:/for:>'
        templatePath=S.getTemplatePath()
        translated=translate_path(Cfg.componentRoot, templatePath)
        d=os.path.dirname(translated)
        os.makedirs(d)
        open(translated, 'w').write(template)
        res=C.stringcomp(templatePath).strip()
        assert res=='', "expected empty, got %s" % res
