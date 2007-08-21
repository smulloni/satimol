import logging
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
        logging.basicConfig(level=logging.DEBUG)
        
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

    def test_layout2(self):
        template="""
        <:slot head:>

        <:slot main:>

        <:slot foot:>

        """
        tp=S.getTemplatePath()
        translated=translate_path(Cfg.componentRoot, tp)
        os.makedirs(os.path.dirname(translated))
        open(translated, 'w').write(template)
        d=os.path.join(Cfg.componentRoot, '/nougat')
        os.mkdir(translate_path(Cfg.componentRoot, d))
        fp=open(os.path.join(translate_path(Cfg.componentRoot, d), 'slotconf.pydcmp'), 'w')
        fp.write("raise ReturnValue(dict(head='HEAD', main='MAIN', foot='FOOT'))\n")
        fp.close()

        fp=C.docroot_open('/nougat/frenchie.stml', 'w')
        fp.write("<:calltemplate:>")
        fp.close()
        slots=S.getConfiguredSlots('/nougat/')
        res=C.stringcomp('/nougat/frenchie.stml', SLOTS=S.getConfiguredSlots('/nougat/'))
        print res
        assert 'HEAD' in res
        assert 'MAIN' in res
        assert 'FOOT' in res