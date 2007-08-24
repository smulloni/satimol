.. -*-rst-*-

=========
 Satimol
=========

Overview
========

"Satimol" is a nickname for the SkunkWeb 4 project, a complete rewrite
of those parts of SkunkWeb 3 that make sense to bring forward into the
modern Python web development world.

Highlights include:

* skunk.cache_, a useful cache for memoization.
* skunk.config_, a configuration system which keeps configuration in
  Python, rather than using INI files or XML.
* skunk.stml_, an implementation of STML (Skunk Template Markup
  Language).
* skunk.web_, a collection of WSGI applications for skunk
  applications.

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

skunk.config
============

Ah, sometime I'll explain this too.

skunk.stml
==========

See stml.txt in the doc/ directory for everything you might
want to know about STML.

skunk.web
=========

DispatchingFileServer is an active page implementation for STML (and
potentially other things).  

Coming up, an MVC framework, and a deployment system.

License
=======

Satimol is available either under the GPL (v3 or later; see COPYING)
or a BSD license (see LICENSE).