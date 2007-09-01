import sys
from traceback import format_exception

import webob.exc import HTTPInternalServerError, HTTPNotFound

from skunk.cache import NO
from skunk.config import Configuration
from skunk.stml import stringcomp
from skunk.util.decorators import rewrap

DEFAULT_ERRORS=webob.exc.status_map.copy()

class NotFound(HTTPNotFound):

    def html_body(self, environ):
        if Configuration.notFoundPage:
            return stringcomp(Configuration.notFoundPage,
                              detail=self.detail,
                              comment=self.comment)
        else:
            return super(NotFound, self).html_body(environ)

DEFAULT_ERRORS[404]=NotFound    

class InternalServerError(HTTPInternalServerError):


    def get_traceback(self):
        if Configuration.showTraceback:
            exc_type, exc_val, exc_traceback=sys.exc_info()
            if exc_val:
                return ''.join(format_exception(exc_type,
                                                exc_val,
                                                exc_traceback))
        return ''

    def html_body(self, environ):
        if Configuration.errorPage:
            tb=self.get_traceback()
            return stringcomp(Configuration.errorPage,
                              traceback=tb)
        else:
            return super(InternalServerError, self).html_body(environ)
        
    
DEFAULT_ERRORS[500]=InternalServerError

Configuration.setDefaults(errorHandlers=DEFAULT_ERRORS,
                          errorPage=None,
                          notFoundPage=None,
                          showTraceback=True)

def errorcatcher(wsgiapp):
    """
    a decorator that catches wsgi errors.
    """
    def newfunc(environ, start_response):
        try:
            retval = wsgiapp(environ, start_response)
        except:
            info = sys.exc_info()
            def newstart(status, headers, exc_info=info):
                return start_response(status, headers, exc_info)
            exc=get_http_exception(httplib.INTERNAL_SERVER_ERROR)
            return exc(environ, newstart)
        else:
            # retval is an iterator, we could wrap it
            # to catch errors in iteration. @TBD
            return retval
            
    return rewrap(wsgiapp, newfunc)


def get_http_exception(status, *args, **kwargs):
    handlerclass=Configuration.errorHandlers[status]
    handler=handlerclass(*args, **kwargs)
    return handler

def handle_error(status, environ, start_response, *args, **kwargs):
    handler=get_http_exception(status, *args, **kwargs)
    return handler(environ, start_response)

    
    

                                     
