import threading

import webob

from skunk.config import Configuration
from skunk.util.hooks import Hook

Context=threading.local()

InitContextHook=Hook()

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
