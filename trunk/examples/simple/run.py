import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration
from skunk.web.context import ContextMiddleware
from skunk.web.controller import expose, ControllerServer
from skunk.web.fileserver  import DispatchingFileServer
from skunk.web.routing import RoutingMiddleware

from someControllers import *

logging.basicConfig(level=logging.DEBUG)

Configuration.load_kw(componentRoot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files'),
                      routes=[
    (('robots', '/robots/:color'), {'controller' : 'home',
                                    'action' : 'robots'}),
    (('wsgi','/wsgi'), {'controller' : 'home', 'action' : 'wsgi'}),
    (('hello', '/hello'), {'controller' : 'home'}),
    ],
                      controllers={'home' : HomeController()},
                      MvcOn=True)

app=ContextMiddleware(RoutingMiddleware(ControllerServer(DispatchingFileServer())))

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')


if __name__=='__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
