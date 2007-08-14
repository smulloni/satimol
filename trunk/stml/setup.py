import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

description="a templating system"

long_description="""

skunk.stml is a standalone implementation of SkunkWeb's STML (Skunk
Template Markup Language), a powerful componentized templating
language.

"""

VERSION='0.2.0'

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      long_description=long_description,
      license="BSD/GPL",
      platforms='OS Independent',
      name="skunk.stml",
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
      keywords="skunk skunkweb STML templating",
      namespace_packages=['skunk'],
      packages=['skunk',
                'skunk.components',
                'skunk.stml',
                'skunk.vfs'],
      install_requires= ['skunk.cache >= 4.0.1'],
      package_dir={'' : 'src'})
