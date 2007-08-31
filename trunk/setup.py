try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup, find_packages

description="caching and templating facilities from the SkunkWeb project"

long_description="""

SaTiMoL is the SkunkWeb 4 project, a set of of libraries and
applications for web development, including a caching system for
memoizing callables, with in-memory, disk, or memcached backends, and
a standalone implementation of SkunkWeb's STML (Skunk Template Markup
Language), a powerful componentized templating language.

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
      name="satimol",
      url="http://code.google.com/p/satimol/",
      classifiers=["Development Status :: 4 - Beta",
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
      keywords="skunk skunkweb STML templating cache WSGI",
      packages=find_packages('src', exclude='tests'),
      entry_points= {
    'console_scripts' : [
    'stmlcc = skunk.stml.cc:main'
    ]
    },
      extras_require= {
    'web' : 'webob',
    'routes' : 'routes',
    'decoratortools' : 'decoratortools'
    },
      package_dir={'' : 'src'},
      test_suite='nose.collector')
