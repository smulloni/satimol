=========
 Satimol
=========

Overview
========

Satimol are the skunk libraries from the skunkweb project, including:

* skunk.cache_, a useful cache for memoization.
* skunk.stml_, an implementation of STML (Skunk Template Markup Language).


skunk.cache
===========

The ``skunk.cache`` package is a simple memoization facility for
callables with in-memory, on-disk, and memcached backends.

An Example
----------


Typical usage::

  >>> from skunk.cache import *
  >>> mycache=DiskCache('/tmp/mycache')
  >>> cache=CacheDecorator(mycache, defaultPolicy=YES)
  >>> @cache(expiration="5m")
  ... def foo(x, y):
  ...    print "actually calculating ...."
  ...    return x + y
  >>> foo(5, 5)
  actually calculating ....
  10
  >>> foo(5, 5)
  10
  

Cache Expiration
----------------

To be explained.

skunk.stml
==========

To be done.





