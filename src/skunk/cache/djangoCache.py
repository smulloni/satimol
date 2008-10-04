import time
import warnings

from django.core.cache import cache as djCache

from skunk.cache.base import Cache

class DjangoCache(Cache):

    def _get_key(self, canonicalName, cacheKey):
        t=(canonicalName, cacheKey)
        return "%s---%s" % t


    def _retrieve(self, canonicalName, cacheKey):
        return djCache.get(self._get_key(canonicalName, cacheKey))

    def _store(self, entry, canonicalName, cacheKey):
        now=time.time()
        entry.stored=now
        expiration=max(now, entry.expiration)-now
        djCache.set(self._get_key(canonicalName, cacheKey), entry, expiration)

    def invalidate(self, canonicalName):

        warnings.warn("cache invalidation is not currently supported by the django backend",
                      NotImplementedWarning)

        

