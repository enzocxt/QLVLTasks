from __future__ import absolute_import

import os
import shutil

from .utilsClass import MetaData
from .Converter import LeNCConverter, TwNCConverter, SoNaRConverter
from .ConverterMulti import LeNCConverterMulti, TwNCConverterMulti, SoNaRConverterMulti


def setup_env(output_dir):
    # create output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # create a tmp directory for xQuery's input (under output directory)
    tmpDIR_dir = '{}/tmpDIR'.format(output_dir)
    if os.path.exists(tmpDIR_dir):
        shutil.rmtree(tmpDIR_dir)
    os.makedirs(tmpDIR_dir)
    # create a tmp directory for intermediate output
    tmpOUT_dir = '{}/tmp'.format(output_dir)
    if os.path.exists(tmpOUT_dir):
        shutil.rmtree(tmpOUT_dir)
    os.makedirs(tmpOUT_dir)

    return tmpDIR_dir, tmpOUT_dir


def clean_env(tmpDIR_dir, tmpOUT_dir):
    os.system("rm -r {}".format(tmpDIR_dir))
    os.system("rm -r {}".format(tmpOUT_dir))


def read_metadata(corpus_name, meta_files=None):
    if corpus_name != 'SoNaR':
        return None
    md = MetaData(meta_files)
    meta_dict = md.read_metadata()
    return meta_dict


def process(corpus_name, input_dir, output_dir, command='', dtd_fname=None, meta_files=None):
    """
    :param corpus_name: LeNC, TwNC, SoNaR
    :param input_dir: the input folder which includes all files you want to process
    :param output_dir: the output folder
    :param command: xQuery command
    :param dtd_fname: dtd filename for corpus LeNC
    :param meta_files: filenames of meta data for corpus SoNaR
    :return:
    """
    # setup environment
    tmpDIR_dir, tmpOUT_dir = setup_env(output_dir)

    # if processing LeNC corpus, dtd file is needed
    if corpus_name == 'LeNC':
        if dtd_fname is None:
            raise AttributeError('Must provide dtd file!')
        else:
            cp_cmd = "cp {} {}".format(dtd_fname, tmpDIR_dir + '/')
            os.system(cp_cmd)

    # read meta data for corpus SoNaR
    meta_dict = read_metadata(corpus_name, meta_files=meta_files)

    if command is None or command == '':
        raise AttributeError("Command should not be empty!")

    mapper = {
        'SoNaR': SoNaRConverter,
        'LeNC': LeNCConverter,
        'TwNC': TwNCConverter,
    }

    # recursively convert corpus files in input directory
    io_paths = (input_dir, tmpDIR_dir, output_dir, tmpOUT_dir)
    converter = mapper[corpus_name]
    converter.convert(io_paths, command=command, meta_dict=meta_dict)

    # clean tmp folders
    clean_env(tmpDIR_dir, tmpOUT_dir)


def process_multi(corpus_name, input_dir, output_dir, command='', dtd_fname=None, meta_files=None):
    """
    :param corpus_name: LeNC, TwNC, SoNaR
    :param input_dir: the input folder which includes all files you want to process
    :param output_dir: the output folder
    :param command: xQuery command
    :param dtd_fname: dtd filename for corpus LeNC
    :param meta_files: filenames of meta data for corpus SoNaR
    :return:
    """
    # setup environment
    tmpDIR_dir, tmpOUT_dir = setup_env(output_dir)

    # read meta data for corpus SoNaR
    meta_dict = read_metadata(corpus_name, meta_files=meta_files)

    if command is None or command == '':
        raise AttributeError("Command should not be empty!")

    mapper = {
        'SoNaR': SoNaRConverterMulti,
        'LeNC': LeNCConverterMulti,
        'TwNC': TwNCConverterMulti,
    }

    # recursively convert corpus files in input directory
    io_paths = (input_dir, tmpDIR_dir, output_dir, tmpOUT_dir)
    converter = mapper[corpus_name]
    converter.convert_multi(input_dir, io_paths, command=command, dtd_fname=dtd_fname, meta_dict=meta_dict)

    # clean tmp folders
    clean_env(tmpDIR_dir, tmpOUT_dir)
