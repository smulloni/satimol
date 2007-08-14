import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

description="a templating system"

long_description="""

skunk.stml is a standalone implementation of SkunkWeb's STML (Skunk
Template Markup Language), a powerful componentized templating
language.

"""

import sys
sys.path.insert(0, 'src')
import skunk.stml
version=skunk.stml.__version__

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      long_description=long_description,
      license="BSD/GPL",
      platforms='OS Independent',
      name="skunk.stml",
      url="http://code.google.com/p/satimol/",
      version=version,
      zip_safe=True,
      keywords="skunk skunkweb STML templating",
      namespace_packages=['skunk'],
      packages=['skunk', 'skunk.components', 'skunk.stml'],
      package_dir={'' : 'src'})
