"""Application module.

Module for common logic for a command line or daemon application.
"""

from builtins import object
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import signal
import sys
import threading

import gflags

from . import util

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('daemon', False,
    'Run application in daemon mode')

gflags.DEFINE_string('pidfile', '',
    "If specified, logs the application's process id to this file.")

gflags.DEFINE_string('logformat',
    '%(asctime)s %(levelname)-8s (%(name)s) %(message)s',
    'Default format to use for log messages.')

gflags.DEFINE_string('logfile',
    '%s.log' % os.path.basename(sys.argv[0].replace('.py','')),
    'Default log file for log messages')

gflags.DEFINE_boolean('log_to_file', False,
    'Send log messages to the log file defined by --logfile')

gflags.DEFINE_boolean('rotate_logs', True,
    'If enabled, logs will be rotated daily at midnight.')

gflags.DEFINE_integer('maximum_log_files', 7,
    'Sets the maximum number of log files to keep around.',
    lower_bound=0)

gflags.DEFINE_boolean('log_to_stdout', True,
    'Send log messages to the console')

gflags.DEFINE_boolean('verbose', os.environ.get('VERBOSE') is not None,
    'Generate extra logging information.',
    allow_override=True)


class App(object):
  """Application instance container.

  Scripts and daemons wishing to reuse the application logic here should
  subclass App, and implement some or all of _Setup and _MainLoop.
  """

  def __init__(self, name='main', daemon=None):
    self._name = name

    try:
      self._extra_argv = FLAGS(sys.argv)  # parse flags
    except gflags.FlagsError as e:
      print('Usage: %s ARGS\n%s\n\nError: %s' % (sys.argv[0], FLAGS, e))
      sys.exit(1)

    if daemon is None:
      daemon = FLAGS.daemon

    self._is_daemon = daemon
    self._do_quit = False
    self._quit_event = threading.Event()
    self._threads = set()

    self._SetupLogging()
    self._SetupSignalHandlers()
    self._logger = logging.getLogger(self._name)

  @classmethod
  def BuildAndRun(cls, name='main'):
    """Convenience class method to create and Start the app."""
    if sys.version_info < (2,4):
      print('kegbot requires Python 2.4 or later; aborting', file=sys.stderr)
      sys.exit(1)

    try:
      app = cls(name)
      app.Start()
    except Exception:
      logger = lambda msg: sys.stderr.write('%s\n' % msg)
      logger('Uncaught exception in app %s. Stack trace:' % name)
      util.LogTraceback(logger)
      logger('Aborting.')
      sys.exit(1)

  def Start(self):
    """Perform setup and run the application main loop."""
    self._Setup()
    self._CheckAndRecordPid()
    self._StartThreads()
    self._MainLoop()
    self._Teardown()

  def _Setup(self):
    """Perform app-specific setup.

    This function is called by Start. Subclasses should call the superclass
    _Setup method (or provide similar functionality.
    """
    if self._is_daemon:
      self._logger.info('Daemon mode requested, switching to background.')
      util.daemonize()
      self._logger.info('Running in background.')

  def _CheckAndRecordPid(self):
    if not FLAGS.pidfile:
      return
    my_pid = os.getpid()
    self._logger.info('Logging PID (%i) to file %s' % (my_pid,
        FLAGS.pidfile))
    if os.path.exists(FLAGS.pidfile):
      self._logger.warning('Pidfile already exists, checking liveness')
      try:
        pid_fd = open(FLAGS.pidfile)
        old_pid = int(pid_fd.readline().strip())
        pid_fd.close()
      except (IOError, ValueError):
        self._logger.error('Could not read pid, abort.')
        sys.exit(1)
      if util.PidIsAlive(old_pid):
        self._logger.error('Old pid %i is still alive, aborting' % old_pid)
        sys.exit(1)

    try:
      pid_fd = open(FLAGS.pidfile, 'w')
      pid_fd.write('%i\n' % my_pid)
      pid_fd.close()
    except IOError:
      self._logger.error('Error writing pid to %s' % FLAGS.pidfile)
      sys.exit(1)

  def _StartThreads(self):
    """Start any threading.Thread objects registered in _threads."""
    if not len(self._threads):
      return
    self._logger.info('Starting all service threads.')
    for thr in self._threads:
      self._logger.info('starting thread "%s"' % thr.getName())
      thr.start()
    self._logger.info('All threads started.')

  def _StopThreads(self):
    """Stop any threading.Thread objects registered in _threads."""
    if not len(self._threads):
      return
    self._logger.info('Stopping all service threads.')
    for thr in self._threads:
      if thr.isAlive():
        self._logger.info('stopping thread "%s"' % thr.getName())
        thr.Quit()
      if thr.isAlive():
        thr.join(2.0)
    self._logger.info('All service threads stopped.')

  def _MainLoop(self):
    """Run the (possibly app-specific) main loop."""
    self._logger.info('Running generic main loop (going to sleep).')
    while not self._do_quit:
      self._quit_event.wait(timeout=1.0)
    self._logger.info('Exiting main loop')

  def _Teardown(self):
    """Clean up before quitting."""
    if FLAGS.pidfile:
      os.unlink(FLAGS.pidfile)

  def _AddAppThread(self, thr):
    """Add a threading.Thread to the set of registered threads.

    Threads added this way will be owned by the app, and automatically started
    and stopped with the main application.
    """
    self._threads.add(thr)

  def Quit(self):
    """Run the (possibly app-specific) Quit routines."""
    self._StopThreads()
    self._TeardownLogging()
    self._do_quit = True
    self._quit_event.set()

  def _SetupLogging(self, level=None):
    if level is None:
      if FLAGS.verbose:
        level = logging.DEBUG
      else:
        level = logging.INFO
    logging.root.setLevel(level)

    # add a file-output handler
    self._logging_file_handler = None
    if FLAGS.log_to_file:
      if FLAGS.rotate_logs:
        self._logging_file_handler = TimedRotatingFileHandler(
            filename=FLAGS.logfile, when='midnight', interval=1,
            backupCount=FLAGS.maximum_log_files)
      else:
        self._logging_file_handler = logging.FileHandler(FLAGS.logfile)
      formatter = logging.Formatter(FLAGS.logformat)
      self._logging_file_handler.setFormatter(formatter)
      logging.root.addHandler(self._logging_file_handler)

    # add tty handler
    self._logging_stdout_handler = None
    if FLAGS.log_to_stdout and not self._is_daemon:
      self._logging_stdout_handler = logging.StreamHandler(sys.stdout)
      formatter = logging.Formatter(FLAGS.logformat)
      self._logging_stdout_handler.setFormatter(formatter)
      logging.root.addHandler(self._logging_stdout_handler)

  def _TeardownLogging(self):
    if self._logging_file_handler:
      logging.root.removeHandler(self._logging_file_handler)
      self._logging_file_handler = None
    if self._logging_stdout_handler:
      logging.root.removeHandler(self._logging_stdout_handler)
      self._logging_stdout_handler = None

  def _SetupSignalHandlers(self):
    """Set up handlers for signals received by main process.

    Sets HUP, INT, QUIT, TERM to quit.
    """
    signal.signal(signal.SIGHUP, self._QuitSignalHandler)
    signal.signal(signal.SIGINT, self._QuitSignalHandler)
    signal.signal(signal.SIGQUIT, self._QuitSignalHandler)
    signal.signal(signal.SIGTERM, self._QuitSignalHandler)

  def _QuitSignalHandler(self, signum, frame):
    """ All handled signals cause a quit """
    self._logger.info('Got signal %i' % signum)
    self.Quit()

