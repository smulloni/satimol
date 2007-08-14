import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

description="a memoization library"

long_description="""

skunk.cache is a simple but robust memoization facility for most
callables with in-memory, on-disk, and memcached backends.  It is the
descendent of the SkunkWeb cache system.  

"""

import sys
sys.path.insert(0, 'src')
import skunk.cache
version=skunk.cache.__version__

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      long_description=long_description,
      license="BSD/GPL",
      platforms='OS Independent',
      name="skunk.cache",
      url="http://code.google.com/p/satimol/",
      version=version,
      zip_safe=True,
      keywords="cache skunk skunkweb",
      namespace_packages=['skunk'],
      packages=['skunk', 'skunk.cache'],
      package_dir={'' : 'src'})
