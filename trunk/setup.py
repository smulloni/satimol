import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, Extension

description="caching and templating facilities from the SkunkWeb project"

long_description="""

SaTiMoL is the latest incarnation of the SkunkWeb libraries, which
include a caching system for memoizing callables, with in-memory,
disk, or memcached backends, and a standalone implementation of
SkunkWeb's STML (Skunk Template Markup Language), a powerful
componentized templating language.


"""

VERSION='0.4.0'

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
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
      version=VERSION,
      ext_modules=[Extension('skunk.util.signal_plus',
                             ['src/skunk/util/signal_plus.c'])],
      keywords="skunk skunkweb STML templating cache",
      packages=['skunk',
                'skunk.cache',
                'skunk.components',
                'skunk.date',
                'skunk.stml',
                'skunk.util',
                'skunk.vfs'],
      package_dir={'' : 'src'},
      test_suite='nose.collector')
