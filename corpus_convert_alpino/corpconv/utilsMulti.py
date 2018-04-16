from __future__ import absolute_import

import os
import logging
import multiprocessing as mp
from tqdm import tqdm

from .utils import copy_to_tmp
from .utilsClass import FilenameGetter, Parser
from .alpino2tabTwNC import alpino2tab as alpino_TwNC
from .alpino2tabLeNC import alpino2tab as alpino_LeNC
from .alpino2tabSoNaR import alpino2tab as alpino_SoNaR
from .alpino2tabUtils import NegativeHeadError


logger = logging.getLogger('[alpino2tab]')


def call_multi(corpus_name, input_root, io_paths, files, meta_dict=None):
    input_dir, _tmpDIR_dir, _output_dir, _tmpOUT_dir = io_paths
    level = input_dir.replace(input_root, '').count(os.sep)
    indent = ' ' * 2 * level
    subindent = ' ' * 2 * (level)

    num_cores = mp.cpu_count() - 1
    num_files = len(files)
    data_group = [[] for _ in range(num_cores)]
    for i in range(num_files):
        idx = i % num_cores
        abs_fname = '{path}{sep}{fname}'.format(path=input_dir, sep=os.sep, fname=files[i])
        data_group[idx].append(abs_fname)

    pool = mp.Pool(processes=num_cores)
    for i in range(num_cores):
        args = (corpus_name, data_group[i], io_paths,)
        kwds = {
            'indent': subindent,
            'meta_dict': meta_dict,
        }
        pool.apply_async(convert_multi, args=args, kwds=kwds)
    pool.close()
    pool.join()


def convert_multi(corpus_name, fnames, io_paths, indent='', meta_dict=None):
    input_dir, output_dir = io_paths

    pid = os.getpid()
    tmpin_dir_proc = '{}{}tmpin_{}'.format(output_dir, os.sep, pid)
    if not os.path.exists(tmpin_dir_proc):
        os.makedirs(tmpin_dir_proc)
    tmpout_dir_proc = '{}{}tmpout_{}'.format(output_dir, os.sep, pid)
    if not os.path.exists(tmpout_dir_proc):
        os.makedirs(tmpout_dir_proc)

    convert_mapping = {
        'TwNC': convert_TwNC,
        'LeNC': convert_LeNC,
        'SoNaR': convert_SoNaR,
    }
    cur_io_paths = (input_dir, tmpin_dir_proc, output_dir, tmpout_dir_proc)
    if corpus_name not in convert_mapping:
        raise AttributeError('Unsupported corpus name: {}!'.format(corpus_name))
    convert = convert_mapping[corpus_name]
    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        args = (fname, cur_io_paths)
        kwargs = {
            'meta_dict': meta_dict,
        }
        try:
            convert(*args, **kwargs)
        except Exception as e:
            logger.error('\ninput file: {}'.format(fname))
            logger.error(e)

    # remove input tmp directory
    os.rmdir(tmpin_dir_proc)
    # remove output tmp directory
    os.rmdir(tmpout_dir_proc)


def convert_TwNC(fname, io_paths, meta_dict=None):
    _input_dir, tmpin_dir_proc, output_dir, tmpout_dir_proc = io_paths
    input_fname = copy_to_tmp(fname, tmpin_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    output_fname = None

    try:
        output_fname = FilenameGetter.get_output_fname_TwNC(tmp_in_fname, output_dir)
    except Exception as e:
        logger.error('\n[Get output filename] input file: \n{}'.format(tmp_in_fname))
        logger.error(e)

    if output_fname is not None:
        try:
            alpino_TwNC(input_fname, output_fname)
        except Exception as e:
            logger.error('\ninput file: {}\noutput file: {}'.format(tmp_in_fname, output_fname.replace(output_dir, '...')))
            logger.error(e)

    os.remove(input_fname)


def convert_LeNC(fname, io_paths, meta_dict=None):
    _input_dir, tmpin_dir_proc, output_dir, tmpout_dir_proc = io_paths

    input_fname = copy_to_tmp(fname, tmpin_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
    output_fname = '{}/{}'.format(tmpout_dir_proc, tmp_out_fname)
    # output_fname = FilenameGetter.get_output_fname_LeNC(tmp_in_fname, output_dir)

    try:
        alpino_LeNC(input_fname, output_fname)
    except Exception as e:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error(e)

    try:
        Parser.split_LeNC(output_fname, output_dir)
    except Exception as e:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error(e)

    os.remove(input_fname)
    os.remove(output_fname)


def convert_SoNaR(fname, io_paths, meta_dict=None):
    _input_dir, tmpin_dir_proc, output_dir, tmpout_dir_proc = io_paths

    input_fname = copy_to_tmp(fname, tmpin_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
    output_fname = '{}/{}'.format(tmpout_dir_proc, tmp_out_fname)

    try:
        alpino_SoNaR(input_fname, output_fname)
    except Exception as e:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error(e)

    # if provided meta_dict (indicating that we are processing SoNaR)
    # split intermediate output into files
    try:
        Parser.parse(output_fname, output_dir, meta_dict)
    except Exception as e:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error(e)

    os.remove(input_fname)
    os.remove(output_fname)
