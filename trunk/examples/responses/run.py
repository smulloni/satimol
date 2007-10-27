import logging
import os

from skunk.config import Configuration
from skunk.web import bootstrap, expose


class BlowController(object):

    @expose()
    def blowup(self):
        raise ValueError, "hey there!"

logging.basicConfig(level=logging.DEBUG)
comproot=os.path.join(os.path.dirname(__file__), 'files')
Configuration.load_kw(componentRoot=comproot,
                      errorPage='/500.html',
                      notFoundPage='/404.html',
                      routes=[
    (('blowup', '/blowup'), {'controller' : 'blow',
                             'action' : 'blowup'})
    ],
                      controllers={'blow' : BlowController()},
                      showTraceback=True)

if __name__=='__main__':
    bootstrap()
