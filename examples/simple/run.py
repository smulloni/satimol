"""
This is a simple example of setting up a skunkweb instance manually,
loading configuration from keywords, rather than from a file,
composing a WSGI application, and serving it (in this case with
cherrypy's wsgi server, but any one can be used).
"""

import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration
from skunk.web.context import ContextMiddleware
from skunk.web.controller import expose, ControllerServer
from skunk.web.fileserver  import DispatchingFileServer
from skunk.web.routing import RoutingMiddleware


class SimpleController(object):

    @expose()
    def index(self):
        return """
        <html>
        <head>
        <titleHome Page</title>
        </head>
        <body>
        <h1>Welcome to Satimol</h1>
        </body>
        </html>
        """

    @expose(content_type='text/plain')
    def robots(self, color):
        return "Your robots are about to turn " + color

    
    @expose()
    def wsgi(self):
        def an_app(environ, start_response):
            start_response('200 OK', [('Content-Type' , 'text/plain')])
            return ['Hello from a WSGI application']
        return an_app

logging.basicConfig(level=logging.DEBUG)

comproot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

Configuration.load_kw(
    componentRoot=comproot,
    routes=[
    (('robots', '/robots/:color'),
     {'controller' : 'simple', 'action' : 'robots'}),
    (('wsgi','/wsgi'),
     {'controller' : 'simple', 'action' : 'wsgi'}),
    (('hello', '/hello'), {'controller' : 'simple'}),
    ],
    controllers={'simple' : SimpleController()},
    MvcOn=True)

app=ContextMiddleware(RoutingMiddleware(ControllerServer(DispatchingFileServer())))

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')


if __name__=='__main__':
    try:
        print "starting server"        
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print "server stopped"
