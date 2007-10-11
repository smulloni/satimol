try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup, find_packages

description="SkunkWeb 4 web framework"

long_description="""

skunk.web is SkunkWeb 4, a set of of libraries and applications for
web development, including:

- a caching system for memoizing callables, with in-memory, disk, or
  memcached backends;

- a standalone implementation of SkunkWeb's venerable STML (Skunk
  Template Markup Language, not to be remembered to be confused with
  Short Term Memory Loss), a powerful componentized templating
  language;

- a lightweight but effective web controller framework.  


"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from skunk import __version__


setup(author="Jacob Smullyan",
      author_email='jsmullyan@gmail.com',
      description=description,
      long_description=long_description,
      license="BSD/GPL",
      platforms='OS Independent',
      name="skunk.web",
      url="http://code.google.com/p/satimol/",
      classifiers=["Development Status :: 3 - Alpha",
                   "Environment :: Web Environment",
                   "Environment :: Web Environment :: Buffet",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Text Processing :: Markup :: HTML',
      ],
      version=__version__,
      keywords="skunk skunkweb STML templating cache WSGI satimol",
      packages=find_packages('src', exclude='tests'),
      entry_points= """
    [console_scripts]
    stmlcc = skunk.stml.cc:main
    skpasswd = skunk.util.authenticator:main

    [python.templating.engines]
    stml = skunk.stml.buffetplugin:BuffetPlugin
    """,
      install_requires=[
    'webob',
    'simplejson',
    'routes',
    'decoratortools'
    ],
      package_dir={'' : 'src'},
      test_suite='nose.collector')
