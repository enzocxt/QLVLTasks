from __future__ import absolute_import

import os
import logging
import functools
import time
import traceback
import codecs
import multiprocessing as mp

from tqdm import tqdm


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        indent = ' ' * len(traceback.extract_stack())
        try:
            logging.debug('{0}entering {1}'.format(indent, fn.__name__))
            return fn(*args, **kwargs)
        except:
            logging.debug('{0}exception in {1}'.format(indent, fn.__name__))
            raise
        else:
            logging.debug('{0}leaving {1}'.format(indent, fn.__name__))

    return wrapper


def timeit(fn):
    @functools.wraps(fn)
    def timer(*args, **kwargs):
        ts = time.time()
        result = fn(*args, **kwargs)
        te = time.time()
        f = lambda arg : type(arg)
        print "\n************************************"
        print "function    = {0}".format(fn.__name__)
        print "  arguments = {0} {1}".format([f(arg) for arg in args], kwargs)
        # print "    return    = {0}".format(result)
        print "  time      = %.6f sec" % (te-ts)
        print "************************************\n"
        return result
    return timer


def list_dir_tree(rootpath):
    for root, dirs, files in sorted(os.walk(rootpath)):
        level = root.replace(rootpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        # subindent = ' ' * 2 * (level + 1)
        num_files = len(files)
        file_info = "{} files".format(num_files)
        dir_info = "{}{}/ ({})".format(indent, os.path.basename(root), file_info)
        print dir_info
        # print "{}{}/".format(indent, os.path.basename(root))
    print ''


def write_file(filename, context):
    with codecs.open(filename, 'w', encoding='latin1') as outf:
        outf.write(context)


def check_fname(filename):
    suffix = filename.split('.')[-1]
    if filename.split('/')[-1].startswith('.'):
        return -1
    elif os.path.isdir(filename):
        return 0
    elif suffix in {'xml', 'gzip'}:
        return 1
    else:
        return -1


def file_filter(path, files):
    res_dirs, res_files = [], []
    for fname in files:
        suffix = fname.split('.')[-1]
        if fname.startswith('.'):
            continue
        elif os.path.isdir('{}/{}'.format(path,fname)):
            res_dirs.append(fname)
        elif suffix in {'xml', 'gzip'}:
            res_files.append(fname)
    return res_dirs, res_files


def copy_to_tmp(filename, tmpdir):
    suffix = filename.split('.')[-1]
    if suffix == 'xml':
        # copy current file into 'tmp' directory
        new_fname = '{}/{}'.format(tmpdir, filename.split('/')[-1])
        cp_cmd = "cp {} {}".format(filename, new_fname)
        os.system(cp_cmd)
        return new_fname
    elif suffix == 'gzip':
        new_fname = '{}/{}'.format(tmpdir, filename.split('/')[-1])
        cp_cmd = "cp {} {}".format(filename, new_fname)
        os.system(cp_cmd)
        xml_fname = new_fname[:-5]
        cmd = "gunzip -S .gzip {}".format(new_fname)
        os.system(cmd)
        return xml_fname
    else:
        return False
