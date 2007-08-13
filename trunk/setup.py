import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, Extension
import os
import sys
sys.path.insert(0, 'src')

version='0.1'
description="an implementation of STML (Skunk Templating Markup Language)"
long_description="""
Satimol is yet another templating language for Python, an implementation of
STML (Skunk Templating Markup Language), the templating language of SkunkWeb.
"""
platforms="OS Independent"

keywords=["templating"]
classifiers=filter(None, """
Development Status :: 4 - Beta
Intended Audience :: Developers
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
""".split('\n'))

setup(author='Jacob Smullyan',
      author_email='jsmullyan@gmail.com',
      url='http://code.google.com/p/satimol',
      description=description,
      long_description=long_description,
      keywords=keywords,
      platforms=platforms,
      license='BSD',
      name='validino',
      version=version,
      zip_safe=True,
      packages=['satimol'],
      package_dir={'' : 'src'},
      test_suite='nose.collector',
      )
      
