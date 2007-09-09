import threading

import webob

from skunk.config import Configuration
from skunk.util.hooks import Hook

# A container for Request, Response, and possibly other things
Context=threading.local()

# A hook for actions before the configuration object is scoped.
# Each function will be passed the environment later passed to
# Configuration.scope(); this is the wsgi environ, with some additional
# keys:
#    url
#    path
PreConfigHook=Hook()

# a hook for actions after the configuration is scoped and the Context
# object has been initialized with Request and Response objects.  Each
# function is passed the Context object and the wsgi environ.
InitContextHook=Hook()

# a hook at the end of request processing for any cleanup operations.  Each
# function is passed the Context object and the wsgi environ.
CleanupContextHook=Hook()

class ContextMiddleware(object):
    """
    middleware that sets up the global Configuration and
    Context objects for the request, and cleans them
    afterwards.
    """

    def __init__(self, app):
        self.app=app

    def __call__(self, environ, start_response):
        req=webob.Request(environ)
        env=environ.copy()
        # add some useful calculated info to env 
        env['url']=req.url
        env['path']=req.path

        PreConfigHook(env)
        
        Configuration.scope(env)
        
        Context.request=req
        Context.response=webob.Response(
            content_type=Configuration.defaultContentType,
            charset=Configuration.defaultCharset,
            server=Configuration.serverIdentification)

        InitContextHook(Context, environ)

        try:
            return self.app(environ, start_response)
        finally:
            CleanupContextHook(Context, environ)
            Context.__dict__.clear()
            Configuration.trim()
    
    
__all__=['Context',
         'InitContextHook',
         'CleanupContextHook',
         'ContextMiddleware']
