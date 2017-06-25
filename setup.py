#!/usr/bin/env python

"""Library of miscellaneous utilities used within Kegbot.
"""

from setuptools import setup, find_packages

VERSION = '0.1.8'
DOCLINES = __doc__.split('\n')
SHORT_DESCRIPTION = DOCLINES[0]
LONG_DESCRIPTION = '\n'.join(DOCLINES[2:])

def setup_package():

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
      install_requires = [
        'isodate',
        'python-gflags >= 1.8',
      ],
      include_package_data = True,
  )

if __name__ == '__main__':
  setup_package()
