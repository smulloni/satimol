"""
<:slot:> and <:calltemplate:> tags, ported from Skunk3's layout service.
"""

import errno
import os
import threading

from skunk.components import (getCurrentDirectory,
                              ComponentHandlingException,
                              call_component,
                              datacomp,
                              rectifyRelativePath)
from skunk.config import Configuration
from skunk.stml.log import exception, warn
from skunk.stml.signature import Signature
from skunk.stml.tags import EmptyTag, BaseTags
from skunk.stml.tagutils import get_temp_name

Configuration.setDefaults(slotConfigFilename='slotconf.pydcmp',
                          defaultTemplate='template.stml',
                          skinDir='/comp/skins',
                          skin='default'
                          )
_slotlocal=threading.local()
def get_slot_stack():
    try:
        return _slotlocal.stack
    except AttributeError:
        stack=[]
        _slotlocal.stack=stack
        return stack
    
def push_slot(slotname):
    get_slot_stack().append(slotname)

def pop_slot(slotname):
    try:
        return get_slot_stack().pop()
    except IndexError:
        warn('pop_slot() called when stack is empty!')
        return None

def getCurrentSlot():
    try:
        return get_slot_stack()[-1]
    except IndexError:
        return None

class ComponentSlot(object):
    '''a wrapper around a component call'''
    def __init__(self,
                 compname,
                 comptype=None,
                 cache=False,
                 expiration=None,
                 namespace=None,
                 **extra):
        self.compname=rectifyRelativePath(compname)
        self.comptype=comptype
        self.cache=cache
        self.expiration=expiration
        self.namespace=namespace
        self.extra=extra

    def __call__(self, **kwargs):
        cache=kwargs.pop('cache', self.cache)
        kwargs.update(self.extra)
        call_component(self.compname,
                       compargs=kwargs,
                       comptype=self.comptype,
                       cache=cache,
                       expiration=self.expiration,
                       namespace=self.namespace)
        

def getTemplatePath(template=None):
    if template is None:
        template=Configuration.defaultTemplate
    return getSkinComponentPath(template)

def getSkinComponentPath(compname):
    return os.path.join(Configuration.skinDir,
                        Configuration.skin,
                        compname)

def getConfiguredSlots(path=None):
    if path is None:
        path=getCurrentDirectory()
        if path is None:
            raise ComponentHandlingException(
                "no file component on component stack and no path provided")

    if not path.endswith('/'):
        path=path+'/'
    slots={}
    slot_conf_name=Configuration.slotConfigFilename
    pathjoin=os.path.join
    conffiles=[pathjoin(path[:(x or 1)], slot_conf_name) \
               for x, y in enumerate(path) if y=='/']
        
    for c in conffiles:
        try:
            newslots=datacomp(c, path=path)
        except IOError, oy:
            if oy.errno==errno.ENOENT:
                # file doesn't exist
                pass
            else:
                exception("error reading slot configuration")
                continue
        else:
            slots.update(newslots)
    return slots
    

class SlotTag(EmptyTag):
    tagName='slot'
    signature=Signature(('name',('slotmap', 'SLOTS')),
                        None,
                        'kwargs')
    modules=[('skunk.stml.layout', '_layout')]


    def genCode(self, codeStream):
        name=self._parsed_args['name']
        slotmap=self._parsed_args['slotmap']
        kwargs=self._parsed_args['kwargs']
        namevar=get_temp_name()
        slotvar=get_temp_name()
        kwargsvar=get_temp_name()
        
        wl=codeStream.writeln
        ind=codeStream.indent
        ded=codeStream.dedent

        
        wl('%s=%r' % (namevar, name))
        wl("%s=%s.get(%s, '')" % (slotvar, slotmap, namevar))
        wl("%s=%r" % (kwargsvar, kwargs))
        wl('__h._layout.push_slot(%s)' % namevar)
        wl('try:')
        ind()
        wl("if callable(%s):" % slotvar)
        ind()
        wl("OUTPUT.write(%s(**%s))" % (slotvar, kwargsvar))
        ded()
        wl("elif %s:" % slotvar)
        ind()
        wl("OUTPUT.write(%s)" % slotvar)
        ded()
        ded()
        wl('finally:')
        ind()
        wl('__h._layout.pop_slot(%s)' % namevar)
        ded()
        wl('del %s' % namevar)
        wl("del %s" % slotvar)
        wl("del %s" % kwargsvar)
        
                           
class CallTemplateTag(EmptyTag):
    tagName='calltemplate'
    signature=Signature((('template', None), ('slotmap', 'SLOTS')),
                        None,
                        'kwargs')
    modules=[('skunk.stml', 'stml'),
             ('skunk.components', 'components')]
    
    def genCode(self, codeStream):
        template=self._parsed_args['template']
        slotmap=self._parsed_args['slotmap']
        kwargs=self._parsed_args['kwargs']

        t=get_temp_name()
        g=get_temp_name()
        K=get_temp_name()
        k=get_temp_name()
        
        wr=codeStream.writeln
        indent=codeStream.indent
        dedent=codeStream.dedent

        wr("if %s is None:" % template)
        indent()
        wr("%s=__h.stml.getTemplatePath()" % t)
        dedent()
        wr("else:")
        indent()
        wr("%s=%s" % (t, template))
        dedent()
          
        wr("try:")
        indent()
        wr(slotmap)
        dedent()
        wr("except NameError:")
        indent()
        wr("%s=__h.stml.getConfiguredSlots()" % slotmap)
        dedent()
        
        wr('%s=globals()' % g)
        # assigning to k assures that it can be deleted later, as
        # if slotmap is empty, then the loop variable won't be initialized!        
        wr("%s=%s=0" % (k, K))
        wr("for %s in %s:" % (k, slotmap))
        indent()
        wr("%s=%s.upper()" % (K, k))
        wr("try:")
        indent()
        wr("%s[%s]=%s[%s]" % (slotmap, k, g, K))
        dedent()
        wr("except KeyError:")
        indent()
        wr("pass")
        dedent()
        dedent()
        wr("del %s, %s, %s" % (g, k, K))
        wr("if %r: " % kwargs)
        indent()
        wr("%s.update(%r)" % (slotmap, kwargs))
        dedent()
        wr("OUTPUT.write(__h.components.include(%s))" % t)
        wr("del %s" % t)
        
BaseTags[CallTemplateTag.tagName]=CallTemplateTag
BaseTags[SlotTag.tagName]=SlotTag


__all__=['getTemplatePath',
         'getConfiguredSlots',
         'getSkinComponentPath',
         'CallTemplateTag',
         'SlotTag',
         'ComponentSlot']
