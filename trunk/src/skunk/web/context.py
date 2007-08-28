import logging
import threading

import webob

from skunk.config import Configuration
from skunk.util.hooks import Hook

Context=threading.local()

log=logging.getLogger(__name__)

ContextInitHook=Hook()
ContextCleanupHook=Hook()

def initContext(environ, force=False):
    
    if not Context.__dict__:
        Context.request=webob.Request(environ)
        Context.response=webob.Response(content_type=Configuration.defaultContentType,
                                        charset=Configuration.defaultCharset)
        # hook for other context munging
        ContextInitHook(environ)

def cleanupContext():
    Context.__dict__.clear()
    ContextCleanupHook()
            

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
        initContext(environ)
        try:
            return self.app(environ, start_response)
        finally:
            cleanupContext()
            Configuration.trim()
    
    
