import logging
import os

#from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration, GlobMatcher
from skunk.web.auth import CookieFileAuthorizer
from skunk.web import ContextMiddleware, DispatchingFileServer, bootstrap

logging.basicConfig(level=logging.DEBUG)

def _relpath(p):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), p)


Configuration.load_kw(componentRoot=_relpath('files'),
                      services=['skunk.web.auth'])
Configuration.addMatcher(GlobMatcher('path', '/protected/*',
                                     authorizer=CookieFileAuthorizer(
    _relpath('auth.conf'),
    'nancynonce',
    '/login.comp')))

app=ContextMiddleware(DispatchingFileServer())

if __name__=='__main__':
    bootstrap(app)

                                     

    
    


