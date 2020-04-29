# Copyright 2008 Mike Wakerly <opensource@hoho.com>
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

"""General purpose utilities, bits, and bobs"""

import asyncore
import collections
import errno
import os
import sys
import threading
import time
import traceback
import logging


class Field:
  """Base field type for use with DeclarativeMetaclass."""


class DeclarativeMetaclass(type):
  """Collect Fields declared on the base classes, and exposes as `.fields`.
  
  Borrowed from django.forms.ModelForm.
  """
  def __new__(mcs, name, bases, attrs):
    fields = []
    for key, value in list(attrs.items()):
      if isinstance(value, Field):
        fields.append((key, value))
        attrs.pop(key)
    attrs['fields'] = collections.OrderedDict(fields)
    new_class = super(DeclarativeMetaclass, mcs).__new__(mcs, name, bases, attrs)
    return new_class

  @classmethod
  def __prepare__(metacls, name, bases, **kwds):
    return collections.OrderedDict()


class KegbotThread(threading.Thread):
  """Convenience wrapper around a threading.Thread"""
  def __init__(self, name):
    threading.Thread.__init__(self)
    self.setName(name)
    self.setDaemon(True)
    self._quit = False
    self._logger = logging.getLogger(self.getName())
    self._thread_started = False

  def hasStarted(self):
    return self._thread_started

  def Quit(self):
    self._quit = True

  def run(self):
    self._thread_started = True
    try:
      self.ThreadMain()
    except:
      self._logger.error('Uncaught exception in thread %s. Stack trace:' %
          self.getName())
      LogTraceback(self._logger.error)
      self._logger.error('Exiting thread.')
      return

  def ThreadMain(self):
    pass


class AsyncoreThread(KegbotThread):
  def ThreadMain(self):
    self._logger.info('Starting up')
    while not self._quit:
      asyncore.loop(timeout=0.5, count=1)
      if not asyncore.socket_map:
        time.sleep(0.5)
    self._logger.info('Quitting')


def daemonize():
  # Fork once
  if os.fork() != 0:
    os._exit(0)
  os.setsid()  # Create new session
  # Fork twice
  if os.fork() != 0:
    os._exit(0)
  #os.chdir("/")
  os.umask(0)

  os.close(sys.__stdin__.fileno())
  os.close(sys.__stdout__.fileno())
  os.close(sys.__stderr__.fileno())

  os.open('/dev/null', os.O_RDONLY)
  os.open('/dev/null', os.O_RDWR)
  os.open('/dev/null', os.O_RDWR)

def str_to_addr(strdata, default_host='127.0.0.1', default_port=0):
  """Extract a tuple of (hostname, port) from a string.

  The string is specified as <hostname>:<port>. If only one value is given, it
  is treated as the <port> and the default ip will be used.
  """

  ip = default_host
  port = default_port

  if strdata is not None:
    parts = strdata.split(':')
    if len(parts) == 2:
      ip, port = parts[0], int(parts[1])
    elif len(parts) == 1:
      port = int(parts[0])

  return ip, port

def synchronized(f):
  """Decorator that synchronizes a class method with self._lock"""
  def new_f(self, *args, **kwargs):
    self._lock.acquire()
    try:
      return f(self, *args, **kwargs)
    finally:
      self._lock.release()
  return new_f

def CtoF(t):
  return ((9.0/5.0)*t) + 32

def PidIsAlive(pid):
  try:
    os.kill(pid, 0)
  except OSError as e:
    if e.errno == errno.ESRCH:
      return False
  return True

def LogTraceback(log_method, tb_tuple=None):
  if tb_tuple is None:
    tb_tuple = sys.exc_info()

  tb_type, tb_value, tb_obj = tb_tuple

  if tb_obj is None:
    log_method('No exception')
    return
  stack = traceback.extract_tb(tb_obj)
  for frame in traceback.format_list(stack):
    for line in frame.split('\n'):
      log_method('    ' + line.strip())
  log_method('Error was: %s: %s' % (tb_type, tb_value))

def get_version(package_name, default='Unknown'):
  """Returns the package version, or default value."""
  try:
    import pkg_resources
    return pkg_resources.get_distribution(package_name).version
  except (ImportError, pkg_resources.DistributionNotFound):
    return default

