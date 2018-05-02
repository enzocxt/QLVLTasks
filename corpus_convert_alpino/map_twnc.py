import os
import sys
import codecs
import time
import shutil
import logging
import functools
import multiprocessing as mp
from tqdm import tqdm

logger = logging.getLogger('[TwNC:split]')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
log_fname = "{}/alpino2tab_TwNC_split.log".format(cur_dir)
file_handler = logging.FileHandler(log_fname)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
std_form = logging.Formatter('')


def timeit(fn):
    @functools.wraps(fn)
    def timer(*args, **kwargs):
        ts = time.time()
        result = fn(*args, **kwargs)
        te = time.time()
        f = lambda arg : type(arg)
        time_info = "\n************************************" + \
                    "\nfunction    = {0}".format(fn.__name__) + \
                    "\n  arguments = {0} {1}".format([f(arg) for arg in args], kwargs) + \
                    "\n  time      = %.6f sec" % (te-ts) + \
                    "\n************************************\n"
        logger.info(time_info)
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
        # print(dir_info)
        logger.info(dir_info)
        # print "{}{}/".format(indent, os.path.basename(root))
    print('')


class CorpusHandler(object):
    def __init__(
            self,
            input_dir,
            output_dir,
            map_file=None
    ):
        """
        :param input_dir: the input folder which includes all files you want to process
        :param output_dir: the output folder
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        if map_file is not None:
            self.map_dict = self.read_mapping(map_file)

    @staticmethod
    def read_mapping(filename):
        mapping = dict()
        with codecs.open(filename, 'r', 'latin-1') as inf:
            for line in inf:
                tok_from, tok_to = line.strip().split('\t')
                tok, pos = tok_to.rsplit('/', 1)
                mapping[tok_from] = tok
        return mapping

    def run_multi(self):

        self.deliver_and_run(self.input_dir)

    def deliver_and_run(self, cur_input_dir, pg_leave=True):
        """
        recursively go to every folder and divide files for parallel methods
        """
        input_root = self.input_dir
        level = cur_input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * level
        files = os.listdir(cur_input_dir)
        dirs, files = file_filter(cur_input_dir, files)

        # call multiprocessing function for files
        if len(files) > 0:
            self.call_multi(cur_input_dir, files)

        # recursively call self for dirs
        dirs = tqdm(sorted(dirs), unit='dir', desc='{}{}'.format(indent, cur_input_dir.split('/')[-1]), leave=pg_leave)
        for d in dirs:
            abs_dir = '{path}{sep}{dir}'.format(path=cur_input_dir, sep=os.sep, dir=d)
            self.deliver_and_run(abs_dir, pg_leave=pg_leave)

    def call_multi(self, input_dir, files):
        input_root = self.input_dir
        level = input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * level
        subindent = ' ' * 2 * level

        num_cores = mp.cpu_count() - 1
        num_files = len(files)
        data_group = [[] for _ in range(num_cores)]
        for i in range(num_files):
            idx = i % num_cores
            abs_fname = '{path}{sep}{fname}'.format(path=input_dir, sep=os.sep, fname=files[i])
            data_group[idx].append(abs_fname)

        # for experiment, only keep one first file in every group
        # data_group = [g[:1] for g in data_group]

        io_paths = (input_root, self.output_dir)
        pool = mp.Pool(processes=num_cores)
        for i in range(num_cores):
            args = (data_group[i], io_paths,)
            kwds = {
                'indent': subindent,
                'map_dict': self.map_dict,
            }
            pool.apply_async(map_multi, args=args, kwds=kwds)
        pool.close()
        pool.join()


def file_filter(path, files):
    res_dirs, res_files = [], []
    for fname in files:
        prefix, ext = os.path.splitext(fname)
        if os.path.isdir('{}/{}'.format(path, fname)):
            res_dirs.append(fname)
        elif ext == '.conll':
            res_files.append(fname)
    return res_dirs, res_files


def map_multi(fnames, io_paths, indent='', map_dict=None):
    input_dir, output_dir = io_paths

    pid = os.getpid()
    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        out_fname = fname.replace(input_dir, output_dir)
        map(fname, out_fname, map_dict=map_dict)


def map(in_fname, out_fname, map_dict=None):
    pardir = os.path.dirname(out_fname)
    # print(pardir)
    os.makedirs(pardir, exist_ok=True)

    '''
    fname, ext = os.path.splitext(out_fname)
    if 'parool_20000316_17' not in fname:
        return
        # print(out_fname)
    '''

    with codecs.open(in_fname, 'r', encoding='latin-1') as inf:
        context = inf.read()
        lines = context.split('\n')
        lines = [clean_and_map(l, map_dict) for l in lines]
        context = '\n'.join(lines)

    with codecs.open(out_fname, 'w', encoding='latin-1') as outf:
        outf.write(context)


def clean_and_map(line, map_dict):
    char = b'\xa0'.decode('latin-1')

    if line.startswith('<'):
        return line
    line.replace(char, '')
    eles = line.split('\t')
    eles = [e.strip() for e in eles]
    if len(eles) < 4:
        return line
    root, pos = eles[2], eles[3]
    root = root.strip()
    token = "{}/{}".format(root, pos)
    if token in map_dict:
        root = map_dict[token]
        eles[2] = root
    return '\t'.join(eles)


@timeit
def main():
    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_mapping"
    input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_split"
    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_split/Netherlands/2000"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_split_v2"
    mapping_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/" \
                    "TwNCLeNC.DifferentLemmaMappings-stefano2.txt"

    # check whether paths exist
    paths = [input_dir, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    corppar = CorpusHandler(input_dir, output_dir, map_file=mapping_fname)
    corppar.run_multi()


if __name__ == '__main__':
    '''
    main()
    '''
    # filename = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_split_v2/Netherlands/2000/parool/parool_20000316_17.conll"
    filename = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/parool_20000316_17.conll"
    with codecs.open(filename, 'r', encoding='latin-1') as inf:
        for line in inf:
            if 'Netelenbos' in line:
                print(line)
                print(line.encode('latin-1'))
    filename = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/test_split/Netherlands/2000/parool/parool_20000316_17.conll"
    with codecs.open(filename, 'r', encoding='latin-1') as inf:
        for line in inf:
            if 'Netelenbos' in line:
                print(line)
                print(line.encode('latin-1'))
