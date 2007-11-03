"""
This example shows how the <:args:> and <:redirect:> tags work.
"""
import os

from skunk.config import Configuration
from skunk.util.pathutil import relpath
from skunk.web import ContextMiddleware, DispatchingFileServer, bootstrap

comproot=relpath(__file__, 'files')

Configuration.load_kw(componentRoot=comproot,
                      showTraceback=True,
                      logConfig={'level' : 'debug'},
                      errorPage='/500.html')

# we don't need a controller for this
app=ContextMiddleware(DispatchingFileServer())


if __name__=='__main__':
    bootstrap(app)
        
