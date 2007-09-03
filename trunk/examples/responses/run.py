import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration
from skunk.web import (ContextMiddleware,
                       ControllerServer,
                       expose,
                       RoutingMiddleware,
                       DispatchingFileServer)



class Controller(object):

    @expose()
    def blowup(self):
        raise ValueError, "hey there!"

    


logging.basicConfig(level=logging.DEBUG)

Configuration.load_kw(componentRoot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files'),
                      errorPage='/500.html',
                      notFoundPage='/404.html',
                      routes=[
    (('blowup', '/'), {'controller' : 'blow',
                      'action' : 'blowup'})
    ],
                      controllers={'blow' : Controller()},
                      MvcOn=True,
                      showTraceback=True)

app=ContextMiddleware(RoutingMiddleware(ControllerServer(DispatchingFileServer())))

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')


if __name__=='__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
