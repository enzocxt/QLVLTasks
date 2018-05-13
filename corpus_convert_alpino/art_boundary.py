# -*- coding: utf-8 -*-

import os
import sys
import codecs
import time
import logging
import functools
import multiprocessing as mp
from collections import OrderedDict
from tqdm import tqdm

logger = logging.getLogger('[TwNC:add boundary]')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
log_fname = "{}/alpino2tab_TwNC_bound.log".format(cur_dir)
file_handler = logging.FileHandler(log_fname)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
std_form = logging.Formatter('')


root_path = os.path.dirname(__file__)


news_dict = {
    'algemeen_dagblad': 'ad',
    'nrc_handelsblad': 'nrc',
    'trouw': 'trouw',
    'parool': 'parool',
    'volkskrant': 'volkskrant',
}


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
    logger.info('')


def file_filter(path, files):
    res_dirs, res_files = [], []
    for fname in files:
        prefix, ext = os.path.splitext(fname)
        if os.path.isdir('{}/{}'.format(path, fname)):
            res_dirs.append(fname)
        elif ext == '.conll':
            res_files.append(fname)
    return res_dirs, res_files


class CorpusHandler(object):
    def __init__(
            self,
            input_dir,
            output_dir,
            art_dir,
    ):
        """
        :param input_dir: the input folder which includes all files you want to process
        :param output_dir: the output folder
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.art_dir = art_dir

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

        io_paths = (input_root, self.output_dir, self.art_dir)
        pool = mp.Pool(processes=num_cores)
        for i in range(num_cores):
            args = (data_group[i], io_paths,)
            kwds = {
                'indent': subindent,
            }
            pool.apply_async(add_bound_multi, args=args, kwds=kwds)
        pool.close()
        pool.join()


def add_bound_multi(fnames, io_paths, indent=''):
    input_dir, output_dir, art_dir = io_paths

    pid = os.getpid()
    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        out_fname = fname.replace(input_dir, output_dir)
        art_fname = get_art_fname(fname, input_dir, art_dir)
        add_bound(fname, art_fname, out_fname)


def get_art_fname(conll_fname, conll_root, art_root):
    path, fname = conll_fname.rsplit(os.sep, 1)
    idx = 0
    for i, c in enumerate(fname):
        if c.isdigit():
            idx = i
            break
    news, date = fname[:idx-1], fname[idx:]
    if news not in news_dict:
        raise ValueError("No such newspaper!")
    fname = '{}{}'.format(news_dict[news], date.replace('conll', 'wpr.art'))
    art_path = path.replace(conll_root, art_root)
    art_path = art_path.replace(news, news_dict[news])
    art_fname = os.path.join(art_path, fname)
    return art_fname


def split_by_tagname(text, tagname):
    """
    split the xml text by tagname
    """
    tags = []
    start = '<{}'.format(tagname)
    end = '</{}>'.format(tagname)
    ls, le = len(start), len(end)
    size = len(text)
    i = 0
    while True:
        idx_start = text.find(start, i)
        idx_end = text.find(end, idx_start)
        if idx_start < 0 or idx_end < 0:
            # tag not found
            break
        tags.append(text[idx_start:(idx_end + le)])
        i = idx_end + le
        if i >= size:
            break

    return tags


def get_sign(sentence, idx):
    lines = sentence.strip().split('\n')
    n = 3   # number of words to compose signature
    i = 0
    sign = []
    for line in lines:
        # eles = line.strip().split('\t')
        eles = line.split('\t')
        if len(eles) <= 2:
            continue
        word = eles[idx]
        word = ''.join(word.strip().split())
        sign.append(word)
        i += 1
        if i == n:
            break
    sign = ''.join(sign)
    return sign


def compare_signs(conll_sents, arts_dict):
    start, end = 0, 0
    for naam, sents in arts_dict.items():
        end = start + len(sents)
        for i, s in enumerate(sents):
            art_sign = get_sign(s, 0)
            conll_sign = get_sign(conll_sents[start + i], 1)
            if art_sign != conll_sign:
                logger.error(s)
                return False
        start = end
    return True


def add_bound_text(conll_sents, arts_dict):
    artikels = []
    start, end = 0, 0
    for naam, sents in arts_dict.items():
        end = start + len(sents)
        sents_text = '\n'.join(conll_sents[start:end])
        start = end
        artikels.append("{}\n{}\n</artikel>".format(naam, sents_text))
    return artikels


def add_bound(conll_fname, art_fname, out_fname):
    if not os.path.exists(art_fname):
        return

    # read conll file and get sentences and signatures
    with codecs.open(conll_fname, 'r', 'latin-1') as inf:
        text = inf.read().strip()
        conll_sents = split_by_tagname(text, 'sentence')
    num_sents = len(conll_sents)
    # conll_signs = [get_sign(s, 1) for s in conll_sents]

    # read art file and get artikels
    with codecs.open(art_fname, 'r', 'latin-1') as inf:
        text = inf.read().strip()
        art_arts = split_by_tagname(text, 'artikel')
        arts_dict = OrderedDict()
        for art in art_arts:
            idx = art.find('>', 1)
            naam = art[:idx+1]
            sents = split_by_tagname(art, 'alpino_ds')
            arts_dict[naam] = sents
    num_alpinos = 0
    for naam, sents in arts_dict.items():
        num_alpinos += len(sents)

    # if num_sents == num_alpinos, we can be sure that sentences are in same order
    # and no sentence is missing between two files
    artikels = []
    print(num_sents, num_alpinos)
    if num_sents == num_alpinos:
        flag = compare_signs(conll_sents, arts_dict)
        if flag:
            artikels = add_bound_text(conll_sents, arts_dict)
            text = '\n'.join(artikels)
            os.makedirs(os.path.dirname(out_fname), exist_ok=True)
            with codecs.open(out_fname, 'w', 'latin-1') as outf:
                outf.write(text)
        else:
            logger.error('\n[Sentence signature inconsistent] file: \n{}'.format(conll_fname))
    elif num_sents - num_alpinos == 1:
        conll_sents = conll_sents[1:]
        flag = compare_signs(conll_sents, arts_dict)
        if flag:
            artikels = add_bound_text(conll_sents, arts_dict)
            text = '\n'.join(artikels)
            os.makedirs(os.path.dirname(out_fname), exist_ok=True)
            with codecs.open(out_fname, 'w', 'latin-1') as outf:
                outf.write(text)
            logger.error('\n[Sentence num diff=1] file: \n{}'.format(conll_fname))
        else:
            logger.error('\n[Sentence num diff=1, signature inconsistent] file: \n{}'.format(conll_fname))
    else:
        logger.error('\n[Sentence number inconsistent] file: \n{}'.format(conll_fname))
    return


def test_add_bound():
    root_path = "/home/enzocxt/Projects/QLVL"

    conll_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/volkskrant_20020305.conll".format(root_path)
    art_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/volkskrant20020305.wpr.art".format(root_path)
    out_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/volkskrant_20020305.conll.bound".format(root_path)
    add_bound(conll_fname, art_fname, out_fname)

    conll_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/nrc_handelsblad_20020215.conll".format(root_path)
    art_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/nrc20020215.wpr.art".format(root_path)
    out_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/nrc_handelsblad_20020215.conll.bound".format(root_path)
    add_bound(conll_fname, art_fname, out_fname)

    conll_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/trouw_20000520.conll".format(root_path)
    art_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/trouw20000520.wpr.art".format(root_path)
    out_fname = "{}/other_tasks/corpus_convert_alpino/test_data/test_bound/trouw_20000520.conll.bound".format(root_path)
    add_bound(conll_fname, art_fname, out_fname)


def main():
    conll_root = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-converted/Netherlands"
    art_root = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-wpr-art"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/TwNC-bound"

    # check whether paths exist
    paths = [conll_root, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(conll_root)
    corppar = CorpusHandler(conll_root, output_dir, art_root)
    corppar.run_multi()


if __name__ == '__main__':
    # test()
    # main()
    test_add_bound()
