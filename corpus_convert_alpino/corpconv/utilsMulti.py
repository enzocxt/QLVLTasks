from __future__ import absolute_import

import os
import logging
import multiprocessing as mp
from tqdm import tqdm

from .utils import copy_to_tmp
from .utilsClass import FilenameGetter, Parser
from .alpino2tab_v2_TwNC import alpino2tab as convert_TwNC
from .alpino2tab_v2_LeNC import alpino2tab as convert_LeNC
from .alpino2tab_v2_SoNaR import alpino2tab as convert_SoNaR
from .alpino2tabUtils import NegativeHeadError


logger = logging.getLogger('[alpino2tab]')
'''
logger.setLevel(logging.INFO)

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
parent_dir = os.path.dirname(cur_dir)
log_fname = "{}/alpino2tab.log".format(parent_dir)

file_handler = logging.FileHandler(log_fname)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
'''

'''
handler_console = 'console'
logger = logging.getLogger('logger')
# console_logger.setLevel(logging.INFO)
# console_logger.addHandler()

# create StreamHandler
console = logging.StreamHandler(stream=None)
console.setLevel(logging.INFO)
logger.addHandler(console)
# create FileHandler
log_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/log.txt"
file_handler = logging.FileHandler(log_fname, mode='w', encoding=None, delay=False)
logger.addHandler(file_handler)
'''


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
        pool.apply_async(alpino2tab_multi, args=args, kwds=kwds)
    pool.close()
    pool.join()


def alpino2tab_multi(corpus_name, fnames, io_paths, indent='', meta_dict=None):
    input_dir, tmpDIR_dir, output_dir, tmpOUT_dir = io_paths

    pid = os.getpid()
    tmpDIR_dir_proc = '{}_{}'.format(tmpDIR_dir, pid)
    if not os.path.exists(tmpDIR_dir_proc):
        os.makedirs(tmpDIR_dir_proc)
    # only for SoNaR
    tmpOUT_dir_proc = '{}_{}'.format(tmpOUT_dir, pid)
    if not os.path.exists(tmpOUT_dir_proc):
        os.makedirs(tmpOUT_dir_proc)

    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        if corpus_name == 'TwNC':
            alpino2tab_TwNC(fname, tmpDIR_dir_proc, output_dir)
        elif corpus_name == 'LeNC':
            alpino2tab_LeNC(fname, tmpDIR_dir_proc, output_dir)
        elif corpus_name == 'SoNaR':
            cur_io_paths = (input_dir, tmpDIR_dir_proc, output_dir, tmpOUT_dir_proc)
            alpino2tab_SoNaR(fname, cur_io_paths, meta_dict=meta_dict)
        else:
            raise AttributeError('Unsupported corpus name: {}!'.format(corpus_name))

    # remove input tmp directory
    os.rmdir(tmpDIR_dir_proc)
    # os.system("rm -r {}".format(tmpDIR_dir_proc))
    # remove output tmp directory only for SoNaR
    os.rmdir(tmpOUT_dir_proc)
    # os.system("rm -r {}".format(tmpOUT_dir_proc))


def alpino2tab_TwNC(fname, tmpDIR_dir_proc, output_dir):
    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    output_fname = FilenameGetter.get_output_fname_TwNC(tmp_in_fname, output_dir)
    try:
        convert_TwNC(input_fname, output_fname)
    except StandardError, e:
        logger.error('\ninput file: {}\noutput file: {}'.format(tmp_in_fname, output_fname.replace(output_dir, '...')))
        logger.error(e)

    # remove input file in tmpDIR_dir
    os.remove(input_fname)


def alpino2tab_LeNC(fname, tmpDIR_dir_proc, output_dir):
    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    output_fname = FilenameGetter.get_output_fname_LeNC(tmp_in_fname, output_dir)
    try:
        convert_LeNC(input_fname, output_fname)
    except NegativeHeadError:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error("Negative value for head")
    except StandardError, e:
        logger.error('\ninput file: {}\noutput file: {}'.format(input_fname, output_fname))
        logger.error(e)

    # remove input file in tmpDIR_dir
    os.remove(input_fname)


def alpino2tab_SoNaR(fname, io_paths, meta_dict=None):
    _input_dir, tmpDIR_dir_proc, output_dir, tmpOUT_dir_proc = io_paths

    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
    output_fname = '{}/{}'.format(tmpOUT_dir_proc, tmp_out_fname)

    pid = os.getpid()
    try:
        convert_SoNaR(input_fname, output_fname)
    except StandardError, e:
        logger.error('\ninput file: {}\noutput file: {} [{}]'.format(input_fname, output_fname, pid))

    # if provided meta_dict (indicating that we are processing SoNaR)
    # split intermediate output into files
    try:
        Parser.parse(output_fname, output_dir, meta_dict)
    except StandardError, e:
        logger.error('\ninput file: {}\noutput file: {} [{}]'.format(input_fname, output_fname, pid))
        logger.error(e)

    # remove input file in tmpDIR_dir
    os.remove(input_fname)
    # remove output file in tmpOUT_dir
    os.remove(output_fname)


def xq_multi(corpus_name, fnames, io_paths, command='', indent='', dtd_fname=None, meta_dict=None):
    input_dir, tmpDIR_dir, output_dir, tmpOUT_dir = io_paths

    pid = os.getpid()
    tmpDIR_dir_proc = '{}_{}'.format(tmpDIR_dir, pid)
    if not os.path.exists(tmpDIR_dir_proc):
        os.makedirs(tmpDIR_dir_proc)
    # only for SoNaR
    tmpOUT_dir_proc = '{}_{}'.format(tmpOUT_dir, pid)
    if not os.path.exists(tmpOUT_dir_proc):
        os.makedirs(tmpOUT_dir_proc)

    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    # if provided dtd file, copy it to this directory
    if corpus_name == 'LeNC':
        if dtd_fname is None:
            raise AttributeError('Should provide dtd file for LeNC corpus!')
        cp_cmd = "cp {} {}".format(dtd_fname, tmpDIR_dir_proc)
        os.system(cp_cmd)

    for fname in fnames:
        if corpus_name == 'TwNC':
            xq_TwNC(fname, tmpDIR_dir_proc, output_dir, command=command)
        elif corpus_name == 'LeNC':
            xq_LeNC(fname, tmpDIR_dir_proc, output_dir, command=command)
        elif corpus_name == 'SoNaR':
            cur_io_paths = (input_dir, tmpDIR_dir_proc, output_dir, tmpOUT_dir_proc)
            xq_SoNaR(fname, cur_io_paths, command=command, meta_dict=meta_dict)
        else:
            raise AttributeError('Unsupported corpus name: {}!'.format(corpus_name))

    # remove input tmp directory
    os.system("rm -r {}".format(tmpDIR_dir_proc))
    # remove output tmp directory only for SoNaR
    os.system("rm -r {}".format(tmpOUT_dir_proc))


def xq_TwNC(fname, tmpDIR_dir_proc, output_dir, command=''):
    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    output_fname = FilenameGetter.get_output_fname_TwNC(tmp_in_fname, output_dir)

    # run xQuery command
    cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir_proc, output_fname)
    status = os.system(cmd)
    if status != 0:  # command does not succeed
        logger.error('\ninput file: {}\noutput file: {}'.format(fname, output_fname))

    # remove input file in tmpDIR_dir
    os.system("rm {}".format(input_fname))
    # we don't have tmp output file for LeNC & TwNC corpus


def xq_LeNC(fname, tmpDIR_dir_proc, output_dir, command=''):
    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    output_fname = FilenameGetter.get_output_fname_LeNC(tmp_in_fname, output_dir)

    # run xQuery command
    cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir_proc, output_fname)
    status = os.system(cmd)
    if status != 0:  # command does not succeed
        logger.error('\ninput file: {}\noutput file: {}'.format(fname, output_fname))

    # remove input file in tmpDIR_dir
    os.system("rm {}".format(input_fname))
    # we don't have tmp output file for TwNC corpus


def xq_SoNaR(fname, io_paths, command='', meta_dict=None):
    _input_dir, tmpDIR_dir_proc, output_dir, tmpOUT_dir_proc = io_paths

    input_fname = copy_to_tmp(fname, tmpDIR_dir_proc)
    tmp_in_fname = input_fname.split('/')[-1]
    tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
    output_fname = '{}/{}'.format(tmpOUT_dir_proc, tmp_out_fname)

    # run xQuery command
    cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir_proc, output_fname)
    status = os.system(cmd)
    if status != 0:  # command does not succeed
        logger.error('\ninput file: {}\noutput file: {}'.format(fname, output_fname))

    # if provided meta_dict (indicating that we are processing SoNaR)
    # split intermediate output into files
    Parser.parse(output_fname, output_dir, meta_dict)

    # remove input file in tmpDIR_dir
    os.system("rm {}".format(input_fname))
    # remove output file in tmpOUT_dir
    os.system("rm {}".format(output_fname))
