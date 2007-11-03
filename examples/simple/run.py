"""
This is a simple example of setting up a skunkweb instance manually,
loading configuration from keywords, rather than from a file,
composing a WSGI application, and serving it (in this case with
cherrypy's wsgi server, but any one can be used).
"""

import os

from skunk.config import Configuration
from skunk.web import expose, bootstrap

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

comproot=os.path.join(os.path.dirname(__file__), 'files')

Configuration.load_kw(
    logConfig=dict(level='debug'),
    componentRoot=comproot,
    routes=[
    (('robots', '/robots/:color'),
     {'controller' : 'simple', 'action' : 'robots'}),
    (('wsgi','/wsgi'),
     {'controller' : 'simple', 'action' : 'wsgi'}),
    (('hello', '/hello'), {'controller' : 'simple'}),
    ],
    controllers={'simple' : SimpleController()})

if __name__=='__main__':
    bootstrap()

