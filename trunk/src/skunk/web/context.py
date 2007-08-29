import threading

import webob

from skunk.config import Configuration

Context=threading.local()

def initContext(environ, force=False):
    
    if not Context.__dict__:
        Context.request=webob.Request(environ)
        Context.response=webob.Response(content_type=Configuration.defaultContentType,
                                        charset=Configuration.defaultCharset,
                                        server=Configuration.serverIdentification)

def cleanupContext():
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
        initContext(environ)
        try:
            return self.app(environ, start_response)
        finally:
            cleanupContext()
            Configuration.trim()
    
    
