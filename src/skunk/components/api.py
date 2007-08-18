"""
Top-level routines for calling components.
"""

from skunk.cache import NO
from skunk.components.exceptions import ComponentHandlingException
from skunk.config import Configuration

def _parse_handle(componentHandle):
    if isinstance(handle, basestring):
        try:
            protocol, handle=handle.split('://', 1)
        except ValueError:
            # fall back on file handler
            return 'file', handle
        else:
            return protocol, handle
    elif callable(handle):
        return 'callable', handle
    else:
        msg='no way to handle %r' % handle
        raise ComponentHandlingException(msg)

def call_component(comp,
                   compargs=None,
                   comptype=None,
                   cache=NO):
    """
    call a component of any type.
    """
    protocol, comp=_parse_handle(comp)
    handler=Configuration.componentHandlers.get(protocol)
    if not handler:
        msg="no handler installed for protocol %r" % protocol
        raise ComponentHandlingException(msg)
    component=handler.createComponent(comp)
    return component(cache=cache, **compargs)
                     
    
def stringcomp(comp, cache=NO, **kwargs):
    """
    call a string component.
    """
    return call_component(comp, kwargs, 'string', cache)
    

def datacomp(comp, cache=NO, **kwargs):
    """
    call a data component.
    """
    return call_component(comp, kwargs, 'data', cache)

def include(comp):
    """
    call an include component.
    """
    return call_component(comp, comptype='include')



__all__=['call_component',
         'stringcomp',
         'datacomp',
         'include']
