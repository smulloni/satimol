import httplib
import logging
import sys
import types

import webob    

from skunk.config import Configuration
from skunk.util.importutil import import_from_string
from skunk.web.context import Context
from skunk.web.util import get_http_exception

log=logging.getLogger(__name__)

Configuration.setDefaults(controllers=[])

def expose(**kwargs):
    def wrapper(func):
        func.exposed=True
        for k,v in kwargs.iteritems():
            setattr(func, k, v)
        return func
    return wrapper
    
def _interpret_response(res):
    """
    coerces the response into a webob.Response object.

    Types accepted:

    - a webob.Response
    - None, in which case Context.response is returned if it has a body,
      and otherwise, a 404
    - a string, which is set to the body of Context.response and the latter
      is returned
    - a unicode string (similar)
    - a list, tuple or generator -- becomes Context.response.app_iter

    Support for return a dict should be added, and invoking the templating
    system directly.
    
    """
    if isinstance(res, webob.Response):
        return res
    ctxt_res=Context.response
    if res is None:
        if ctxt_res.app_iter or ctxt_res.body:
            # something has been done to it
            return ctxt_res
        else:
            # perhaps this implicit behavior is
            # less good than simply returning
            # an empty response.... @REEXAMINE
            return None
    elif isinstance(res, str):
        ctxt_res.body=res
        return ctxt_res
    elif isinstance(res, unicode):
        ctxt_res.unicode_body=res
        return ctxt_res
    elif isinstance(res, (list,tuple,types.GeneratorType)):
        ctxt_res.app_iter=res
        return ctxt_res
    elif isinstance(res, int):
        try:
            return get_http_exception(res)
        except KeyError:
            pass
    # last resort
    try:
        ctxt_res.body=str(res)
    except:
        pass
    return get_http_exception(httplib.NOT_FOUND)    

def dispatch_from_environ(environ, next_app=None):
    """
    dispatch according to the wsgi routing specification
    """
    try:
        tmp=environ['wsgiorg.routing_args']
    except KeyError:
        return None
    else:
        margs, mkwargs=tmp
    return dispatch(*margs, **mkwargs)

def dispatch(*args, **kwargs):
    controller=kwargs.get('controller')
    if not controller:
        return

    if isinstance(controller, basestring):
        try:
            controller=import_from_string(controller)
        except ImportError:
            return get_http_exception(httplib.SERVER_ERROR,
                                      comment="couldn't import controller %s" % controller)
        
    action=kwargs.get('action', 'index')    
    meth=getattr(controller, action, None)
    if not meth:
        return 

    if not getattr(meth, 'exposed', False):
        log.info("request for method that isn't exposed, not honoring")
        return
    
    try:
        res=meth(*args, **kwargs)
    except webob.exc.HTTPException, e:
        res=e

    return _interpret_response(res)

class Punt(Exception):
    pass

class ControllerServer(object):

    def __init__(self, wrapped_app=None):
        self.wrapped_app=wrapped_app

    def __call__(self, environ, start_response):
        try:
            res=dispatch_from_environ(environ)
        except Punt:
            res=None
        if res is None and self.wrapped_app:
            return self.wrapped_app(environ, start_response)
        else:
            return handle_error(httplib.NOT_FOUND,
                                environ,
                                start_response)
            
        
            

            
                                
        
        

    
    
    
