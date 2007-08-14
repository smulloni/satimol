import unittest
import random
import time
import tempfile
import sys
import shutil

from skunk.cache import *

class CacheTest(unittest.TestCase):
    def _func(x, y, z):
        return random.randrange(x, y), random.randrange(y, z)
    _func=staticmethod(_func)
    
    def setUp(self):
        self.memorycache=MemoryCache()
        self.diskcache=DiskCache(tempfile.mkdtemp())

    def tearDown(self):
        p=self.diskcache.path
        del self.diskcache
        shutil.rmtree(p)

    def test_no_mem(self):
        cache=self.memorycache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        NO,
                        time.time()+5)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        NO,
                        time.time()+5)
        assert res1.value!=res2.value

    def test_no_disk(self):
        cache=self.diskcache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        NO,
                        time.time()+5)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        NO,
                        time.time()+5)
        assert res1.value!=res2.value

    def test_yes_mem(self):
        cache=self.memorycache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+5)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+5)
        assert res1.value==res2.value

    def test_yes_disk(self):
        cache=self.diskcache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+5)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+5)
        assert res1.value==res2.value

    def test_expiration_mem(self):
        cache=self.memorycache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+1)
        time.sleep(1.05)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+1)
        assert res1.value!=res2.value

    def test_expiration_disk(self):
        cache=self.diskcache
        res1=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+1)
        time.sleep(1.05)
        res2=cache.call(self._func,
                        dict(x=1, y=50, z=200),
                        YES,
                        time.time()+1)
        assert res1.value!=res2.value

if __name__=='__main__':
    unittest.main()
