from __future__ import absolute_import

import os
import traceback
from tqdm import tqdm

from .utils import file_filter
from .utilsMulti import call_multi


class ConverterMulti(object):

    @classmethod
    def convert_multi(cls, *args, **kwargs):
        pass


class SoNaRConverterMulti(ConverterMulti):
    _corpus_name = 'SoNaR'

    @classmethod
    def convert_multi(cls, input_root, io_paths, command='', dtd_fname=None, meta_dict=None, pg_leave=True):
        input_dir, tmpDIR_dir, output_dir, tmpOUT_dir = io_paths
        level = input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * (level)
        files = os.listdir(input_dir)
        dirs, files = file_filter(input_dir, files)

        # call multiprocessing function for files
        if len(files) > 0:
            call_multi(cls._corpus_name, input_root, io_paths, files,
                       meta_dict=meta_dict)

        # recursively call self for dirs
        dirs = tqdm(sorted(dirs), unit='dir', desc='{}{}'.format(indent, input_dir.split('/')[-1]), leave=pg_leave)
        for d in dirs:
            abs_dir = '{path}{sep}{dir}'.format(path=input_dir, sep=os.sep, dir=d)
            cur_io_paths = (abs_dir, tmpDIR_dir, output_dir, tmpOUT_dir)
            cls.convert_multi(input_root, cur_io_paths, command=command, meta_dict=meta_dict)


class LeNCConverterMulti(ConverterMulti):
    _corpus_name = 'LeNC'

    @classmethod
    def convert_multi(cls, input_root, io_paths, command='', dtd_fname=None, meta_dict=None, pg_leave=True):
        input_dir, tmpDIR_dir, output_dir, tmpOUT_dir = io_paths
        level = input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * level
        files = os.listdir(input_dir)
        dirs, files = file_filter(input_dir, files)

        # call multiprocessing function for files
        if len(files) > 0:
            call_multi(cls._corpus_name, input_root, io_paths, files)

        # recursively call self for dirs
        dirs = tqdm(sorted(dirs), unit='dir', desc='{}{}'.format(indent, input_dir.split('/')[-1]), leave=pg_leave)
        for d in dirs:
            abs_dir = '{path}{sep}{dir}'.format(path=input_dir, sep=os.sep, dir=d)
            cur_io_paths = (abs_dir, tmpDIR_dir, output_dir, tmpOUT_dir)
            cls.convert_multi(input_root, cur_io_paths, command=command, dtd_fname=dtd_fname)


class TwNCConverterMulti(ConverterMulti):
    _corpus_name = 'TwNC'

    @classmethod
    def convert_multi(cls, input_root, io_paths, command='', dtd_fname=None, meta_dict=None, pg_leave=True):
        input_dir, tmpDIR_dir, output_dir, tmpOUT_dir = io_paths
        # depth = len(traceback.extract_stack()) - 3
        level = input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * level

        files = os.listdir(input_dir)
        dirs, files = file_filter(input_dir, files)

        # call multiprocessing function for files
        if len(files) > 0:
            call_multi(cls._corpus_name, input_root, io_paths, files)

        # recursively call self for dirs
        dirs = tqdm(sorted(dirs), unit='dir', desc='{}{}'.format(indent, input_dir.split('/')[-1]), leave=pg_leave)
        for d in dirs:
            abs_dir = '{path}{sep}{dir}'.format(path=input_dir, sep=os.sep, dir=d)
            cur_io_paths = (abs_dir, tmpDIR_dir, output_dir, tmpOUT_dir)
            cls.convert_multi(input_root, cur_io_paths, command=command, pg_leave=pg_leave)
