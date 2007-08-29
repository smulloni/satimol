from os.path import splitext, dirname, join as pathjoin

from skunk.config import Configuration
from skunk.components.api import getCurrentDirectory, rectifyRelativePath
from skunk.components.context import ComponentContext
from skunk.components.objects import *


class ComponentHandler(object):
    """
    abstract base class for component handlers
    """
    protocols=()

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        """
        returns the appropriate component class for the
        createComponent call
        """
        raise NotImplemented

    def inferComponentType(self, componentHandle):
        """
        if possible, infer the component type from the handle,
        or raise ValueError.
        """
        raise ValueError, "cannot infer component type"

    def instantiateComponent(self,
                             kls,
                             componentHandle,
                             namespace,
                             **extra):
        return kls(componentHandle,
                   namespace=namespace,
                   **extra)

    
    def createComponent(self,
                        protocol,
                        componentHandle,
                        componentType,
                        namespace=None,
                        **extra):
        if protocol not in self.protocols:
            raise ValueError, "unsupported protocol: %s" % protocol
        if componentType is None:
            # this should raise a ValueError if the type cannot
            # inferred; it shouldn't return None
            componentType=self.inferComponentType(componentHandle)
            assert componentType
        kls=self.getComponentClass(protocol,
                                   componentHandle,
                                   componentType)

        stack=ComponentContext.componentStack
        if (not namespace) and componentType=='include':
            if not stack:
                raise ComponentHandlingException,\
                      "include not possible without something on component stack!"
            namespace=stack[-1].namespace

        return self.instantiateComponent(kls,
                                         componentHandle,
                                         namespace,
                                         **extra)


class CallableComponentHandler(ComponentHandler):
    """
    A component handler for generic callables.
    """
    protocols=('callable',)

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        """
        returns the appropriate component class for the
        createComponent call
        """
        if componentType in ('string', 'include'):
            return StringOutputComponent
        elif componentType=='data':
            return Component
        raise ValueError, "unknown component type: %s" % componentType

    def instantiateComponent(self,
                             kls,
                             componentHandle,
                             namespace,
                             **extra):
        if isinstance(componentHandle, tuple):
            name=componentHandle[0]
            code=componentHandle[1]
        else:
            name=getattr(componentHandle,
                         '__name__',
                         repr(componentHandle))
            code=componentHandle
        return kls(code=componentHandle,
                   name=name,
                   namespace=namespace,
                   **extra)


DEFAULT_FILE_COMPONENT_SUFFIX_MAP={
    '.pycomp' : ('string', StringOutputFileComponent),
    '.pydcmp' : ('data',  FileComponent),
    '.pyinc' : ('include', StringOutputFileComponent),
    '.py' : ('string', StringOutputFileComponent),
    }

class FileComponentHandler(ComponentHandler):
    """
    a component handler for file components.
    """
    protocols=('file',)
    

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        compClass=self._lookup_suffix(componentHandle)[1]
        if compClass:
            return compClass
        else:
            raise ValueError, "no handler for handle: %r" % componentHandle
            

    def _lookup_suffix(self, handle):
        return Configuration.componentFileSuffixMap.get(splitext(handle)[1], (None, None))
    
    def inferComponentType(self, componentHandle):
        compType=self._lookup_suffix(componentHandle)[0] 
        if compType:
            return compType
        else:
            raise ValueError, \
                  "cannot infer component type from file name %r" % componentHandle

    def instantiateComponent(self,
                             kls,
                             componentHandle,
                             namespace,
                             **extra):
        componentHandle=rectifyRelativePath(componentHandle)
        return kls(componentHandle,
                   namespace=namespace,
                   **extra)

defaultComponentHandlers=dict(callable=CallableComponentHandler(),
                              file=FileComponentHandler())

__all__=['ComponentHandler',
         'FileComponentHandler',
         'CallableComponentHandler',
         'DEFAULT_FILE_COMPONENT_SUFFIX_MAP',
         'defaultComponentHandlers']
