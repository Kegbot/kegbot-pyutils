#!/usr/bin/env python

"""Unittest for kbjson module"""

import datetime
import pytz
import unittest

from . import kbjson
from . import util

TIMEZONE = pytz.timezone('America/Los_Angeles')

SAMPLE_DECODE = """
{
  "event": "my-event",
  "sub" : {
    "list" : [1,2,3]
  },
  "iso_time": "2010-06-11T23:01:01-08:00",
  "bad_time": "123-45"
}
"""

SAMPLE_ENCODE = {
  'time': datetime.datetime(2010, 6, 11, 23, 1, 1, tzinfo=TIMEZONE),
  'notatime': '123',
}

class JsonTestCase(unittest.TestCase):
  def testDecode(self):
    obj = kbjson.loads(SAMPLE_DECODE)
    self.assertEqual(obj.event, "my-event")
    self.assertEqual(obj.sub.list, [1,2,3])

    expected = datetime.datetime(2010, 6, 11, 23, 1, 1, tzinfo=TIMEZONE)
    self.assertEqual(obj.iso_time, expected)
    self.assertEqual(obj.bad_time, "123-45")  # fails strptime

  def testEncode(self):
    s = kbjson.dumps(SAMPLE_ENCODE)
    self.assertTrue('"time": "2010-06-11T23:01:01-08:00"' in s)

  def testTransitivity(self):
    self.assertEqual(SAMPLE_ENCODE, kbjson.loads(kbjson.dumps(SAMPLE_ENCODE)))

if __name__ == '__main__':
  unittest.main()

