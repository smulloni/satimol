import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

description="software components"

long_description="""

skunk.components is 

"""

import sys
sys.path.insert(0, 'src')
import skunk.components
version=skunk.cache.__version__

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      long_description=long_description,
      license="BSD/GPL",
      platforms='OS Independent',
      name="skunk.components",
      url="http://code.google.com/p/satimol/",
      version=version,
      zip_safe=True,
      keywords="skunk skunkweb",
      namespace_packages=['skunk'],
      packages=['skunk', 'skunk.components'],
      package_dir={'' : 'src'})
