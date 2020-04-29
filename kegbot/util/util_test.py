#!/usr/bin/env python

"""Unittest for util module"""

import unittest
from . import util

class MiscTestCase(unittest.TestCase):
  def testGetVersion(self):
    version = util.get_version('bogus', 'foo')
    self.assertEqual('foo', version)

if __name__ == '__main__':
  unittest.main()
