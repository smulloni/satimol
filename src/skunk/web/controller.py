import logging
import sys
import traceback

from skunk.config import Configuration
from skunk.util.importutil import import_from_string
from skunk.web.context import Context

log=logging.getLogger(__name__)

Configuration.setDefaults(controllers=[])

def handle_error(message,
                 method,
                 controller,
                 action,
                 args,
                 kwargs):
    res=Configuration.errorHandlers[500]()
    # do something here
    return res


def dispatch_from_environ(environ, next_app=None):
    try:
        tmp=environ['wsgiorg.routing_args']
    except KeyError:
        return None
    else:
        margs, mkwargs=tmp
    return dispatch(next_app=next_app, *margs, **mkwargs)

def dispatch(next_app=None, *args, **kwargs):
    controller=kwargs.get('controller')
    if not controller:
        return 
    action=kwargs.get('action', 'index')
    if isinstance(controller, basestring):
        try:
            controller=import_from_string(controller)
        except ImportError:
            handle_error("dispatcher couldn't import name '%s'" % controller,
                         None,
                         controller,
                         action,
                         args,
                         kwargs)
            
    
    meth=getattr(controller, action, None)
    if meth:
        if not getattr(meth, 'exposed', False):
            log.info("request for method that isn't exposed, not honoring")
            return
        try:
            res=meth(*args, **kwargs)
        except webob.exc.HTTPException, e:
            res=e
        except:
            exc=sys.exc_info()[
            return handle_error("error in controller method",
                                meth,
                                controller,
                                action,
                                args,
                                kwargs)
        
        if isinstance(res, webob.Response):
            return res
        if isinstance(res, str):
            gres=Context.response
            gres.body=res
            return gres
        elif isinstance(res, unicode):
            gres=Context.response
            gres.unicode_body=res
            return gres
        elif isinstance(res, (list,tuple)):
            gres=Context.response
            gres.app_iter=res
            return gres
        elif isinstance(res, int):
            try:
                return Configuration.errorHandlers[res]()
            except KeyError:
                return str(res)


    
    
    
