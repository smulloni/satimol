"""
support code for using routes middleware.
"""
import httplib

from routes import request_config
import routes.middleware

from skunk.config import Configuration
from skunk.web.context import Context, InitContextHook
from skunk.web.exceptions import get_http_exception

Configuration.setDefaults(MvcOn=True,
                          routes=[],
                          controllers={})

def _redirect(url, status=httplib.MOVED_PERMANENTLY):
    raise get_http_exception(status, location=url)

def initMapper(context, environ):
    if not Configuration.MvcOn:
        return
    map=routes.Mapper()
    for r in Configuration.routes:
        if isinstance(r, dict):
            map.connect(**r)
        elif isinstance(r, (list, tuple)):
            if (len(r)==2 and
                isinstance(r[0], (list, tuple)) and
                isinstance(r[1], dict)):
                map.connect(*r[0], **r[1])
            else:
                map.connect(*r)
        else:
            raise ValueError, "wrong arguments for connect()"

    map.create_regs(list(Configuration.controllers))
    context.routes_mapper=map
    request_config().redirect=_redirect

# initial the mapper in the context middleware
InitContextHook.append(initMapper)

class RoutingMiddleware(routes.middleware.RoutesMiddleware):
    """
    trivial subclass of routes' own middleware
    """

    def __init__(self, app, use_method_override=False, path_info=True):
        super(RoutingMiddleware, self).__init__(app,
                                                None,
                                                use_method_override,
                                                path_info)

    def mapper():
        def fget(self):
            return Context.routes_mapper
        def fset(self, val):
            pass
        return fget, fset
    mapper=property(*mapper())

    def __call__(self, environ, start_response):
        if not Configuration.MvcOn:
            return self.app(environ, start_response)
        return super(RoutingMiddleware, self).__call__(environ, start_response)

            
__all__=['RoutingMiddleware']
