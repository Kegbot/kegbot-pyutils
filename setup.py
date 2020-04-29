from setuptools import setup, find_packages
import pathlib

VERSION = '1.0.0'
BASE_DIR = pathlib.Path(__file__).parent
README = (BASE_DIR / 'README.md').read_text()

setup(
  name='kegbot-pyutils',
  version=VERSION,
  description='Python utilities used in the Kegbot Project',
  long_description=README,
  long_description_content_type='text/markdown',
  author='The Kegbot Project Contributors',
  author_email='info@kegbot.org',
  license='MIT',
  url='https://kegbot.org/',
  packages=find_packages(exclude=['testdata']),
  namespace_packages=['kegbot'],
  install_requires=[
    'python-gflags >= 1.8',
  ],
  include_package_data=True,
)
