from __future__ import absolute_import

import os
import traceback
from tqdm import tqdm

from .utils import check_fname, copy_to_tmp
from .utilsClass import FilenameGetter, Parser


class Converter(object):

    @classmethod
    def convert(cls, *args, **kwargs):
        pass


class SoNaRConverter(Converter):
    _corpus_name = 'SoNaR'

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, meta_dict=meta_dict, pg_leave=False)
                continue

            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
            output_fname = '{}/{}'.format(tmpOUT_dir, tmp_out_fname)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            # print cmd
            os.system(cmd)

            # split intermediate output into files
            Parser.parse(output_fname, output_dir, meta_dict)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # remove output file in tmpOUT_dir
            os.system("rm {}".format(output_fname))


class LeNCConverter(Converter):
    _corpus_name = 'LeNC'

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, meta_dict=None, pg_leave=False)
                continue

            # in_filename has only filename without system path
            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            output_fname = FilenameGetter.get_output_fname_LeNC(tmp_in_fname, output_dir)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            os.system(cmd)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # as we don't have tmp output file for TwNC corpus
            # we do not need to remove output file in tmpOUT_dir


class TwNCConverter(Converter):
    _corpus_name = 'TwNC'

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, pg_leave=False)
                continue

            # in_filename has only filename without system path
            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            output_fname = FilenameGetter.get_output_fname_TwNC(tmp_in_fname, output_dir)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            os.system(cmd)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # as we don't have tmp output file for TwNC corpus
            # we do not need to remove output file in tmpOUT_dir
