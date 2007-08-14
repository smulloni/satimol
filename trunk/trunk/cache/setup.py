import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

description="skunk.cache is a robust memoization facility."

setup(author="Jacob Smullyan",
      author_email='smulloni@smullyan.org',
      description=description,
      license="BSD/GPL",
      name="skunk.cache",
      url="http://code.google.com/p/satimol/",
      version="4.0.1",
      zip_safe=True,
      keywords="cache skunk skunkweb",
      namespace_packages=['skunk'],
      packages=['skunk', 'skunk.cache'],
      package_dir={'' : 'src'})
