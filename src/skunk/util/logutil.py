import logging
import sys

def loginit(offset=1, all=False):
    g=sys._getframe(offset).f_locals
    name=g['__name__']
    l=logging.getLogger(name)
    g['logger']=l
    g['debug']=l.debug
    m=('critical',
       'debug',
       'error',
       'exception',
       'info',
       'log',
       'warn')
    for x in m:
        g[x]=getattr(l,x)
    if all:
        g['__all__']=m + ('logger',)


    
        
