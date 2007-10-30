import logging
import threading

import webob

from skunk.config import Configuration
from skunk.util.hooks import Hook

log=logging.getLogger(__name__)

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

# a hook at the end of request processing, after CleanupContextHook,
# for cleanup operations of resources like database connections.  Each
# function is passed the Context object and the wsgi environ.
CleanupResourcesHook=Hook()


class ContextMiddleware(object):
    """
    middleware that sets up the global Configuration and
    Context objects for the request, and cleans them
    afterwards.
    """

    def __init__(self, app):
        self.app=app

    def _runapp(self, app, environ, start_response):
        try:
            return app(environ, start_response)
        finally:
            try:
                try:
                    CleanupContextHook(Context, environ)
                except:
                    log.exception('error in CleanupContextHook')

                try:
                    CleanupResourcesHook(Context, environ)
                except:
                    log.exception('error in CleanupResourcesHook')
                
            finally:
                Context.__dict__.clear()
                Configuration.trim()
        

    def __call__(self, environ, start_response):
        if not hasattr(Context, 'wsgiapp'):
            Context.wsgiapp=self
        
        req=webob.Request(environ)
        env=environ.copy()
        # add some useful calculated info to env 
        env['url']=req.url
        env['path']=req.path

        try:
            PreConfigHook(env)
        except webob.exc.HTTPException, exc:
            return self._runapp(exc, environ, start_response)
        
        Configuration.scope(env)

        Context.request=req
        Context.response=webob.Response(
            content_type=Configuration.defaultContentType,
            charset=Configuration.defaultCharset,
            server=Configuration.serverIdentification)

        try:
            InitContextHook(Context, environ)
        except webob.exc.HTTPException, exc:
            return self._runapp(exc, environ, start_response)

        return self._runapp(self.app, environ, start_response)

    
    
__all__=['Context',
         'InitContextHook',
         'CleanupContextHook',
         'PreConfigHook',
         'ContextMiddleware']
