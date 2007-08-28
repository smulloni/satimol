import logging

import routes

log=logging.getLogger(__name__)

def getMapper():
    return routes.Mapper()

def get_match_and_route(environ):
    config=routes.request_config()
    config.mapper=getMapper()
    config.environ=environ
    return config.mapper_dict, config.route

def clean_routes_config():
    config=routes.request_config()
    try:
        del config.environ
    except AttributeError:
        log.error("expected routes request config to have an 'environ' attribute")
        
    

class RoutingMiddleware(object):

    def __init__(self, app):
        self.app=app

    def __call__(self, environ, start_response):
        config=routes.request_config()
        config.mapper=mapper
        config.environ=environ
        match=config.mapper_dict
        route=config.route
        if match:
            for k,v in match.iteritems():
                if v and isinstance(v, basestring):
                    match[k]=urllib.unquote_plus(v)
        environ['wsgiorg.routing_args']=((), match)
        environ['routes.route']=route

        if match.get('path_info'):
            oldpath = environ['PATH_INFO']
            newpath = match.get('path_info') or ''
            environ['PATH_INFO'] = newpath
            if not environ['PATH_INFO'].startswith('/'):
                environ['PATH_INFO'] = '/' + environ['PATH_INFO']
            environ['SCRIPT_NAME'] += re.sub(r'^(.*?)/' + newpath + '$', 
                                             r'\1', oldpath)
            if environ['SCRIPT_NAME'].endswith('/'):
                environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'][:-1]
        try:
            return self.app(environ, start_response)
        finally:
            del config.environ
            del config.mapper.environ
        
