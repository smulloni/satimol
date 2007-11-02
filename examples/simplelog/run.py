"""
This uses the logconfig service with minimal customization.
"""
import logging
import os

from skunk.config import Configuration
from skunk.web import expose, bootstrap

@expose(content_type='text/plain')
def index():
    return "A truly pleasant experience\n"

Configuration.load_kw(
    services=['skunk.web.logconfig'],
    logConfig={'level' : logging.DEBUG,
               'filename' : 'debug.log'},
    routes=[
    ((':action',),{'controller' : 'main'}),
    ],
    controllers={'main' : __name__})

if __name__=='__main__':
    bootstrap()

