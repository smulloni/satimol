import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration, GlobMatcher
from skunk.web.auth import CookieFileAuthorizer, enable as enable_auth
from skunk.web.context import ContextMiddleware
from skunk.web.fileserver import DispatchingFileServer

logging.basicConfig(level=logging.DEBUG)

def _relpath(p):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), p)

# load the authentication service; must be done explicitly
enable_auth()

Configuration.load_kw(componentRoot=_relpath('files'))
Configuration.addMatcher(GlobMatcher('path', '/protected/*',
                                     authorizer=CookieFileAuthorizer(
    _relpath('auth.conf'),
    'nancynonce',
    '/login.comp')))

app=ContextMiddleware(DispatchingFileServer())

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')


if __name__=='__main__':
    try:
        print "starting server"        
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print "server stopped"
                                     

    
    


