"""
Top-level routines for calling components.
"""

from skunk.cache import NO, decode
from skunk.components.context import ComponentContext
from skunk.components.exceptions import ComponentHandlingException
from skunk.config import Configuration

def _parse_handle(handle):
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
                   cache=NO,
                   expiration=None,
                   namespace=None):
    """
    call a component of any type.
    """
    protocol, comp=_parse_handle(comp)
    handler=Configuration.componentHandlers.get(protocol)
    if not handler:
        msg="no handler installed for protocol %r" % protocol
        raise ComponentHandlingException(msg)
    component=handler.createComponent(protocol, comp, comptype, namespace)
    return component(compargs,
                     cachePolicy=decode(cache),
                     expiration=expiration)

                     
    
def stringcomp(comp, cache=NO, expiration=None, namespace=None, **kwargs):
    """
    call a string component.
    """
    return call_component(comp, kwargs, 'string', cache, expiration, namespace)
    

def datacomp(comp, cache=NO, expiration=None, namespace=None, **kwargs):
    """
    call a data component.
    """
    return call_component(comp, kwargs, 'data', cache, expiration, namespace)

def include(comp):
    """
    call an include component.
    """
    return call_component(comp, comptype='include')


def getCurrentComponent():
    stack=ComponentContext.componentStack
    if stack:
        return stack[-1]

def getCurrentDirectory():
    for c in reversed(ComponentContext.componentStack):
        try:
            f=c.filename
        except AttributeError:
            continue
        else:
            return dirname(f)
    


__all__=['call_component',
         'stringcomp',
         'datacomp',
         'include',
         'getCurrentComponent',
         'getCurrentDirectory']
