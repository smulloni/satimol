"""
<:slot:> and <:calltemplate:> tags.

While the rest of this package has managed to avoid, so far, any
references to configuration, it is no longer possible for that to be
the case.  We need to know here a document root; we need to know a
default template.

"""

import errno

from skunk.config import Configuration
from skunk.stml.log import exception
from skunk.stml.signature import Signature
from skunk.stml.tags import EmptyTag
from skunk.stml.tagutils import get_temp_name

Configuration.mergeDefaults(slotConfigFilename='slotconf.pydcmp')


def getConfiguredSlots(path=None) 
    if path is None:
        path=current_component()

    elif not path.endswith('/'):
        path=path+'/'
    slots={}
    slot_conf_name=Configuration.slotConfigFilename
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
        
    signature=Signature(('name',('slotmap', 'SLOTS')),
                        None,
                        'kwargs')

    def genCode(self, codeStream):
        name=self._parsed_args['name']
        slotmap=self._parsed_args['slotmap']
        kwargs=self._parsed_args['kwargs']
        slotvar=get_temp_name()
        codeStream.writeln("%s=%s.get(%s, '')" % (slotvar, slotmap, name))
        codeStream.writeln("if callable(%s):" % slotvar)
        codeStream.indent()
        codeStream.writeln("OUTPUT.write(%s(**%r))" % (slotvar, kwargs))
        codeStream.dedent()
        codeStream.writeln("elif %s:" % slotvar)
        codeStream.indent()
        codeStream.writeln("OUTPUT.write(%s)" % slotvar)
        codeStream.dedent()
        codeStream.writeln("del %s" % slotvar)
                           
class CallTemplateTag(EmptyTag):
    signature=Signature((('template', None), ('slotmap', 'SLOTS')),
                        None,
                        'kwargs')
    
    def genCode(self, codeStream):
        template=self._parsed_args['template']
        slotmap=self._parsed_args['slotmap']
        kwargs=self._parsed_args['kwargs']

        """
        if template is None:
            tempvar=getTemplatePath()
        else:
            tempvar=template
        try:
            SLOTS
        except NameError:
            SLOTS=getConfiguredSlots()
        
        """
        t=get_temp_name()
        g=get_temp_name()
        K=get_temp_name()
        k=get_temp_name()
        
        wr=codeStream.writeln
        indent=codeStream.indent
        dedent=codeStream.dedent

        wr("if %s is None:" % template)
        indent()
        wr("%s=__h.slotutils.getTemplatePath()" % t)
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
        wr("%s=__h.slotutils.getConfiguredSlots()" % slotmap)
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
        wr("%s.update(%r)" % (slotmap, kw))
        dedent()
        wr("OUTPUT.write(COMPONENT.callIncludeComponent(%s))" % template)
        wr("del %s" % template)
        
