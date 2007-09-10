"""

This contains a Cache implementation for storing the
compiled code of components.  It is used internally
in the Component class, and an instance can be
passed to a Component constructor.

  >>> c=CompileCache('/path/to/cacheroot', useMemory=True)
  >>> component=FileComponent(mypath, compileCache=c)

The cache can store compiled code on disk, in memory, or both.

"""

import os
import errno
import stat
import time
import marshal
normpath=os.path.normpath

from skunk.config import Configuration
from skunk.util.logutil import loginit; loginit()

def _mtime(path):
    try:
        s=os.stat(path)
    except OSError, e:
        if e.errno!=errno.ENOENT: 
           raise
        return None 
    else:
        return max(s[stat.ST_CTIME],
                   s[stat.ST_MTIME])

class _default(object): pass

class CompileCache(object):
    def __init__(self,
                 cacheroot=_default,
                 useMemory=_default,
                 componentRoot=_default):
        self._cacheroot=cacheroot
        self._useMemory=useMemory
        self._componentRoot=componentRoot
        self._mem={}

    def cacheroot():
        def fget(self):
            if self._cacheroot == _default:
                return Configuration.compileCachePath
            return self._cacheroot
        return fget
    cacheroot=property(cacheroot())

    def useMemory():
        def fget(self):
            if self._useMemory == _default:
                return Configuration.useCompileMemoryCache
            return self._useMemory
        return fget
    useMemory=property(useMemory())

    def componentRoot():
        def fget(self):
            if self._componentRoot == _default:
                return Configuration.componentRoot
            return self._componentRoot
        return fget
    componentRoot=property(componentRoot())

    def getCompiledCode(self, component):
        # is the component file-based?
        try:
            lastmod=component.__lastmodified__
        except AttributeError:
            lastmod=None

        entry=self._retrieve(component.name)
        if entry:
            cachemod, code=entry
            if lastmod is None or lastmod<=cachemod:
                return code

        code=component.compile(component.getCode())
        self._store(component.name, code)
        return code

    def _retrieve(self, name):
        name='%s%s' % (self.componentRoot, name)
        use_mem=self.useMemory
        cacheroot=self.cacheroot
        if (not use_mem) and (not cacheroot):
            warn('compile cache is neither using memory nor a cacheroot!')
        if use_mem:
            try:
                return self._mem[name]
            except KeyError:
                pass
        if cacheroot:
            f=normpath('%s/%sc' % (cacheroot, name))
            cachemod=_mtime(f)
            if cachemod:
                stuff=file(f).read()
                code=marshal.loads(stuff)
                if use_mem:
                    self._mem[name]=cachemod, code
                return cachemod, code

    def _store(self, name, code):
        name='%s%s' % (self.componentRoot, name)
        use_mem=self.useMemory
        cacheroot=self.cacheroot
        if (not use_mem) and (not cacheroot):
            warn('compile cache is neither using memory nor a cacheroot!')        
        if use_mem:
            self._mem[name]=(time.time(), code)
        if cacheroot:
            f=normpath('%s/%sc' % (cacheroot, name))
            d=os.path.dirname(f)
            if not os.path.exists(d):
                os.makedirs(os.path.dirname(f))
            fp=file(f, 'wb')
            fp.write(marshal.dumps(code))
            fp.close()


__all__=['CompileCache']
