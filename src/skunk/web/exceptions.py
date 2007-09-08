import logging
import string
import sys
from traceback import format_exception

from webob.exc import HTTPInternalServerError, HTTPNotFound, status_map

from skunk.cache import NO
from skunk.config import Configuration
from skunk.components import stringcomp

log=logging.getLogger(__name__)

DEFAULT_ERRORS=status_map.copy()

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
        tb=self.get_traceback()
        if Configuration.errorPage:
            return stringcomp(Configuration.errorPage,
                              traceback=tb)
        else:
            return self.default_500_body(tb)

    def default_500_body(self, tb):
        t=string.Template('<h2>$title</h2>$explanation<br />$detail<br /><pre>$traceback</pre>$comment')
        args=dict(explanation=self.explanation or '',
                  detail=self.detail or '',
                  comment=self.comment or '',
                  title=self.title,
                  traceback=tb)
        return t.substitute(args)
              
    
DEFAULT_ERRORS[500]=InternalServerError

Configuration.setDefaults(errorHandlers=DEFAULT_ERRORS,
                          errorPage=None,
                          notFoundPage=None,
                          showTraceback=True)

def get_http_exception(status, *args, **kwargs):
    handlerclass=Configuration.errorHandlers[status]
    handler=handlerclass(*args, **kwargs)
    return handler

def handle_error(status, environ, start_response, *args, **kwargs):
    handler=get_http_exception(status, *args, **kwargs)
    return handler(environ, start_response)

__all__=['DEFAULT_ERRORS', 'get_http_exception']
