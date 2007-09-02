from skunk.web.controller import expose
from skunk.web.context import Context

class HomeController(object):

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

    @expose()
    def robots(self, color):
        Context.response.content_type='text/plain'
        return "Your robots are about to turn " + color

    
    @expose()
    def wsgi(self):
        def an_app(environ, start_response):
            start_response('200 OK', [('Content-Type' , 'text/plain')])
            return ['Hello from a WSGI application']
        return an_app
