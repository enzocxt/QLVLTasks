from __future__ import absolute_import

import os
import sys
import logging


'''
default_handler = logging.StreamHandler('sys.stderr')
default_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
'''

logger = logging.getLogger('[alpino2tab]')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
parent_dir = os.path.dirname(cur_dir)
log_fname = "{}/alpino2tab.log".format(parent_dir)
file_handler = logging.FileHandler(log_fname)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
# std_form = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')
std_form = logging.Formatter('')
console_handler.setFormatter(std_form)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)


def get_logger():
    logger.info("test for stream handler...")
    return logger


def create_logger(app):
    """
    Get the 'flask.app' logger and configure it if needed.

    When :attr:`~flask.Flask.debug` is enabled, set the logger level to
    :data:`logging.DEBUG` if it is not set.

    If there is no handler for the logger's effective level, add a
    :class:`~logging.StreamHandler` for
    :func:`~flask.logging.wsgi_errors_stream` with a basic format.
    """
    logger = logging.getLogger('convert')

    return logger

'''
class LogState(object):

    def __init__(self):
        self.indentation = 0


_log_state = LogState()
_log_state.indentation = 0


@contextlib.contextmanager
def indent_log(num=2):
    """
    A context manager which will cause the log output to be indented fro any
    log messages emitted inside it
    """
    _log_state.indentation += num
    try:
        yield
    finally:
        _log_state.indentation -= num


def get_indentation():
    return getattr(_log_state, 'indentation', 0)


class IndentingFormatter(logging.Formatter):

    def format(self, record):
        """
        Calls the standard formatter, but will indent all of the log messages
        by our current indentation level.
        """
        formatted = logging.Formatter.format(self, record)
        formatted = ''.join([
            (' ' * get_indentation()) + line
            for line in formatted.splitlines(True)
        ])
        return formatted


class ColorizedStreamHandler(logging.StreamHandler):

    def __init__(self, stream=None):
        logging.StreamHandler.__init__(self, stream)

    def format(self, record):
        msg = logging.StreamHandler.format(self, record)

        return msg
'''
