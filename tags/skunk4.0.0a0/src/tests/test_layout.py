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
        logging.basicConfig(level=logging.DEBUG)
        
    def setUp(self):
        self.componentRoot=tempfile.mkdtemp()
        Cfg.load_kw(componentRoot=self.componentRoot,
                    useCompileMemoryCache=False)



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
        res=C.stringcomp('/nougat/frenchie.stml') 
        assert 'HEAD' in res
        assert 'MAIN' in res
        assert 'FOOT' in res

    def test_buffet1(self):
        template="""
        <:slot slot1:>
        <:slot slot2:>
        """
        tp=S.getTemplatePath()
        translated=translate_path(Cfg.componentRoot, tp)
        os.makedirs(os.path.dirname(translated))
        open(translated, 'w').write(template)
        plugin=S.BuffetPlugin()
        res=plugin.render(info=dict(SLOTS=dict(slot1='hello', slot2='goodbye')))
        assert 'hello' in res
        assert 'goodbye' in res
        
