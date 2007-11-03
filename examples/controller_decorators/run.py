import os

from skunk.config import Configuration
from skunk.web import bootstrap, expose, template

@expose(content_type='text/plain')
def helloworld(name):
    return 'Hello, World, and furthermore, hi there %s' % name

@template('/witch.comp')
@expose()
def dingdong():
    return dict(witch='Brenda',
                status='dead or missing')

Configuration.load_kw(
    logConfig=dict(level='debug'),
    componentRoot=os.path.join(os.path.dirname(__file__), 'files'),
    routes=[
    (('hi', 'helloworld/:name'),
     dict(controller='daone', action='helloworld')),
    (('ding', 'dingdong'),
     dict(controller='daone', action='dingdong')),
    ],
    controllers={'daone' : __name__},
    showTracebacks=True)


if __name__=='__main__':
    bootstrap()
