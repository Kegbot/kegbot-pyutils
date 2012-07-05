#!/usr/bin/env python
"""Library of miscellaneous utilities used within Kegbot.
"""

VERSION = '0.1.4'
DOCLINES = __doc__.split('\n')
SHORT_DESCRIPTION = DOCLINES[0]
LONG_DESCRIPTION = '\n'.join(DOCLINES[2:])

def setup_package():
  from distribute_setup import use_setuptools
  use_setuptools()
  from setuptools import setup, find_packages

  setup(
      name = 'kegbot-pyutils',
      version = VERSION,
      description = SHORT_DESCRIPTION,
      long_description = LONG_DESCRIPTION,
      author = 'mike wakerly',
      author_email = 'opensource@hoho.com',
      url = 'http://kegbot.org/',
      packages = find_packages(exclude=['testdata']),
      namespace_packages = ['kegbot'],
      scripts = [
        'distribute_setup.py',
      ],
      install_requires = [
        'python-gflags >= 1.8',
        'pytz',
      ],
      include_package_data = True,
  )

if __name__ == '__main__':
  setup_package()
