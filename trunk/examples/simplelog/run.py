"""
This uses the logconfig service with minimal customization.
"""
import os

from skunk.config import Configuration
from skunk.web import expose, bootstrap

@expose(content_type='text/plain')
def index():
    return "A truly pleasant experience\n"

Configuration.load_kw(
    logConfig={'level' : 'debug',
               'filename' : 'debug.log'},
    routes=[
    ((':action',),{'controller' : 'main'}),
    ],
    controllers={'main' : __name__})

if __name__=='__main__':
    bootstrap()

