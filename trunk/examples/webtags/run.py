"""
This example shows how the <:args:> and <:redirect:> tags work.
"""
import logging
import os

logging.basicConfig(level=logging.DEBUG)

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration
from skunk.web import ContextMiddleware, DispatchingFileServer

comproot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

Configuration.load_kw(componentRoot=comproot,
                      showTraceback=True,
                      errorPage='/500.html')

# we don't need a controller for this
app=ContextMiddleware(DispatchingFileServer())

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')

if __name__=='__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        
