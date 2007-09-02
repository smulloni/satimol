import threading

import webob

from skunk.config import Configuration
from skunk.util.hooks import Hook

Context=threading.local()

InitContextHook=Hook()

CleanupContextHook=Hook()

def initContext(environ, force=False):
    if force or not Context.__dict__:
        Context.request=webob.Request(environ)
        Context.response=webob.Response(content_type=Configuration.defaultContentType,
                                        charset=Configuration.defaultCharset,
                                        server=Configuration.serverIdentification)
        InitContextHook(Context, environ)

def cleanupContext():
    CleanupContextHook()
    Context.__dict__.clear()
            
class ContextMiddleware(object):
    """
    middleware that sets up the global Configuration and
    Context objects for the request, and cleans them
    afterwards.
    """

    def __init__(self, app):
        self.app=app

    def __call__(self, environ, start_response):
        Configuration.scope(environ)
        initContext(environ, True)
        try:
            return self.app(environ, start_response)
        finally:
            cleanupContext()
            Configuration.trim()
    
    
