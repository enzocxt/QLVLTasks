from __future__ import absolute_import

import contextlib
import logging
import logging.handlers
import os


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
