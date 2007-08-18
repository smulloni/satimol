import threading

import skunk.cache as cache
from skunk.config import Configuration
from skunk.components.compileCache import CompileCache

class _component_context(threading.local):
    # no need for this to be thread-local
    compileCache=CompileCache()
    
    def componentStack():
        def fget(self):
            try:
                return self._componentStack
            except AttributeError:
                stack=[]
                self._componentStack=stack
                return stack
            
        return fget
    componentStack=property(componentStack())


    def componentCache():
        def fget(self):
            conf=Configuration.componentCache
            if not conf:
                return None
            if isinstance(conf, cache.Cache):
                return conf
            elif not isinstance(conf, basestring):
                raise TypeError("expected a string, got %r" % conf)
            try:
                cachedict=self._cachedict
            except AttributeError:
                cachedict=self._cachedict={}
            if conf in cachedict:
                return cachedict[conf]

            if conf==':memory:':
                c=cachedict[conf]=cache.MemoryCache()

            elif conf.startswith('memcached://'):
                # example: 'memcached://127.0.0.1:5000,192.168.1.240:3000'
                prot, servers=conf.split('//:', 1)
                servers=servers.split(',')
                dbg=Configuration.componentCacheDebugMemcached
                c=cachedict[conf]=cache.MemcachedCache(servers, dbg)
                    
            else:
                c=cachedict[conf]=DiskCache(conf)
                
            return c
        return fget
    componentCache=property(componentCache())



ComponentContext=_component_context()

__all__=['ComponentContext']

