import httplib
import logging
import sys
import types

import simplejson
import webob    

from skunk.config import Configuration
from skunk.util.decorators import rewrap
from skunk.util.importutil import import_from_string
from skunk.web.context import Context
from skunk.web.exceptions import get_http_exception, handle_error

log=logging.getLogger(__name__)

def expose(**response_attrs):
    """
    a decorator which marks a controller function or method
    as a public action.  It can also be used to set attributes
    on the webob.Response.
    """
    def wrapper(func):
        func.exposed=True
        func.response_attrs=response_attrs
        return func
    return wrapper

def _interpret_response(res, meth):
    """
    coerces the response into a webob.Response object.

    Types accepted:

    - a webob.Response or callable
    - None, in which case Context.response is returned 
    - a string, which is set to the body of Context.response and the latter
      is returned
    - a unicode string (similar)
    - if content type is application/json and type is list, tuple, or dict,
      data will be json-ed and put in Context.response, which is returned
    - a list, tuple or generator -- becomes Context.response.app_iter
    - an integer is taken to be an HTTP status code and a default error
      response is generated.  An invalid code will cause an error.

    Anything else is turned in a string with str().

    This will also set attributes on response that have been set with the
    @expose decorator, but only if the context response is used; if another
    response is returned, those values will be ignored.
    
    """
    if isinstance(res, webob.Response):
        return res
    elif callable(res):
        # should be a WSGI application
        return res
    ctxt_res=Context.response
    if res is None:
        log.warn("returning None from controller action, returning context response")
        return ctxt_res
    # some response metadata may be set in the expose decorator
    # (perhaps too much -- for instance, "body".  If you do that,
    # it's your problem)
    response_attrs=getattr(meth, 'response_attrs', {})
    for k, v in response_attrs.iteritems():
        setattr(ctxt_res, k, v)
    
    if isinstance(res, str):
        ctxt_res.body=res
        return ctxt_res
    elif isinstance(res, unicode):
        ctxt_res.unicode_body=res
        return ctxt_res
    elif ctxt_res.content_type=='application/json' \
             and isinstance(res, (list,tuple,dict)):
        ctxt_res.body=simplejson.dumps(res)
        return ctxt_res
    elif isinstance(res, (list,tuple,types.GeneratorType)):
        ctxt_res.app_iter=res
        return ctxt_res
    elif isinstance(res, int):
        try:
            return get_http_exception(res)
        except KeyError:
            log.error("returning unrecognized http status code from controller: %d",
                     res)
            raise
    # last resort
    log.debug(("got unusual type, %s, as return value from action, "
               "stringifying as last resort"),
              type(res))
    ctxt_res.body=str(res)
    return ctxt_res


def dispatch_from_environ(environ, next_app=None):
    """
    dispatch according to the wsgi routing specification
    """
    try:
        tmp=environ['wsgiorg.routing_args']
    except KeyError:
        log.debug("no routing_args found")
        return None
    else:
        margs, mkwargs=tmp
    return dispatch(environ, *margs, **mkwargs)

def dispatch(environ, *args, **kwargs):
    log.debug("in dispatch")
    controller_name=kwargs.pop('controller', None)
    if not controller_name:
        log.debug("no controller found")
        return

    controller=Configuration.controllers.get(controller_name)
    if not controller:
        log.warn('no such controller found: %s', controller_name)
        return
    if isinstance(controller, basestring):
        try:
            controller=import_from_string(controller)
        except ImportError:
            return get_http_exception(httplib.INTERNAL_SERVER_ERROR,
                                      comment="couldn't import controller %s" % controller)
    else:
        log.debug("got a non-string for controller: %s", controller)
    action=kwargs.pop('action', 'index')
    reqmeth=environ['REQUEST_METHOD']
    if reqmeth=='HEAD':
        reqmeth='GET'
    method_qualified_action='%s_%s' % (action, reqmeth)
    meth=getattr(controller, method_qualified_action, None)
    if not meth:
        meth=getattr(controller, action, None)
    if not meth:
        log.debug(("no controller action found "
                   "(looked for action %s in controller %s)"),
                  action, controller)
        return 

    if not getattr(meth, 'exposed', False):
        log.info("request for method that isn't exposed, not honoring")
        return
    log.debug("method is %s", meth)
    try:
        res=meth(*args, **kwargs)
    except webob.exc.HTTPException, e:
        res=e
    return _interpret_response(res, meth)

class Punt(Exception):
    pass

class ControllerServer(object):

    def __init__(self, wrapped_app=None):
        self.wrapped_app=wrapped_app

    def __call__(self, environ, start_response):
        try:
            try:
                res=dispatch_from_environ(environ)
            except Punt:
                res=None

            if res is None:
                if self.wrapped_app:
                    return self.wrapped_app(environ, start_response)
                else:
                    return handle_error(httplib.NOT_FOUND,
                                        environ,
                                        start_response)

            return res(environ, start_response)
        except:
            return handle_error(httplib.INTERNAL_SERVER_ERROR,
                                environ,
                                start_response)
            
        
__all__=['expose', 'Punt', 'ControllerServer']
                                
