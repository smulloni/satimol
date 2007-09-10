from skunk.components import (StringOutputComponent,
                              StringOutputFileComponent, 
                              DEFAULT_FILE_COMPONENT_SUFFIX_MAP, 
                              FileComponentHandler,
                              CallableComponentHandler)
from skunk.config import Configuration
from skunk.stml.parser import parse as stml_parse
from skunk.stml.tags import BaseTags
from skunk.stml.codeStream import PythonCodeOutputStream
from skunk.stml.tagutils import import_into
from skunk.util.timeconvert import convert





class _namespaceholder:
    pass


class STMLComponentMixin(object):
    """
    This inserts into the namespace two objects that are used to store
    values needed by STML: __h, the "hidden namespace", where modules
    and global objects may be stored; and __t, the "temporary
    namespace", where temporary values may be stored.  These objects
    should not be used in user code; they exist entirely to assist in
    keeping the user namespace clean.
    """
    _hidden_nses={}
    _temporary_nses={}
    
    def __init__(self, tagVocabulary=None):
        """
        An STML component implementation.
        """
        self.tagVocabulary=tagVocabulary or BaseTags
        self._tagset=frozenset(self.tagVocabulary.values())
        alltags=set()
        for t in self._tagset:
            alltags.add(t)
            alltags.update(t.localTagDict.values())
        self._alltags=alltags
        if len(self._tagset)!=len(self.tagVocabulary):
            raise ValueError, "duplicate tag in tagVocabulary!"

    def _precall(self, namespace):
        namespace.update(dict(__h=self._get_hidden_namespace(),
                              __t=self._get_temporary_namespace()))
        return namespace

    def _get_hidden_namespace(self):
        """
        populates the hidden namespace with all modules needed by the
        available tags, as indicated by the tags' "modules"
        attributes.  The hidden namespace is created once and cached
        globally for all components that share the same set of tags.
        """
        try:
            ret=self._hidden_nses[self._tagset]
        except KeyError:
            ret=_namespaceholder()
            modset=set()
            for t in self._alltags:
                modset.update(t.modules)
                
            for m in modset:
                try:
                    m, asname=m
                except (ValueError, TypeError):
                    import_into(ret, m)
                else:
                    import_into(ret, m, asname)
            self._hidden_nses[self._tagset]=ret
            
        return ret

    def _get_temporary_namespace(self):
        """
        Called by the constructor, this initializes the temporary
        namespace for every instance by calling the tag classmethod
        _init_temporary_namespace() on every tag with the new
        temporary namespace object.
        """
        ret=_namespaceholder()
        for t in self._alltags:
            t._init_temporary_namespace(ret)
        return ret
        

    def getCode(self):
        """
        returns generated Python code for the component.
        """
        code=getattr(self, '_code', None)
        if code:
            return code
        
        stml=self.getSTML()
        node=stml_parse(stml, self.tagVocabulary)
        codeStream=PythonCodeOutputStream()
        for k in node.children:
            if isinstance(k, basestring):
                codeStream.writeln('OUTPUT.write(%r)' % k)
            else:
                k.genCode(codeStream)
        code=self._code=codeStream.getvalue()
        return code

    def getSTML(self):
        """
        returns the STML source of the component.
        """
        try:
            return self._stml
        except AttributeError:
            self._stml=self._get_code_raw()
            return self._stml


class STMLComponent(STMLComponentMixin, StringOutputComponent):
    def __init__(self,
                 stmlcode,
                 name=None,
                 namespace=None,
                 tagVocabulary=None):
        STMLComponentMixin.__init__(self, tagVocabulary)
        StringOutputComponent.__init__(self,
                                       code=stmlcode,
                                       name=name)

    def _precall(self, namespace):
        namespace=STMLComponentMixin._precall(self, namespace)
        return StringOutputComponent._precall(self, namespace)

class STMLFileComponent(STMLComponentMixin, StringOutputFileComponent):
    def __init__(self,
                 filename,
                 namespace=None,
                 tagVocabulary=None):
        STMLComponentMixin.__init__(self, tagVocabulary)
        StringOutputFileComponent.__init__(self,
                                           filename,
                                           namespace=namespace)

    def _precall(self, namespace):
        namespace=STMLComponentMixin._precall(self, namespace)
        return StringOutputFileComponent._precall(self, namespace)            


DEFAULT_STML_FILE_COMPONENT_SUFFIX_MAP={
    '.comp' : ('string', STMLFileComponent),
    '.inc' : ('include', STMLFileComponent),
    '.stml' : ('string', STMLFileComponent),
    '.html' : ('string', STMLFileComponent),
    }

DEFAULT_STML_FILE_COMPONENT_SUFFIX_MAP.update(DEFAULT_FILE_COMPONENT_SUFFIX_MAP)

Configuration.setDefaults(
    componentFileSuffixMap=DEFAULT_STML_FILE_COMPONENT_SUFFIX_MAP)

__all__=['STMLComponentMixin',
         'STMLComponent',
         'STMLFileComponent',
         'DEFAULT_STML_FILE_COMPONENT_SUFFIX_MAP']



