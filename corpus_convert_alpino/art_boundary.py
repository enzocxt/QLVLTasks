# -*- coding: utf-8 -*-

"""
This file adds article boundaries to converted conll files
"""

import os
import sys
import codecs
import logging
from collections import OrderedDict

from artUtils import *

# logging settings
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


# root_path = os.path.dirname(__file__)


def add_bound_multi(fnames, io_paths, indent=''):
    input_dir, output_dir, art_dir = io_paths

    pid = os.getpid()
    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        # out_fname = fname.replace(input_dir, output_dir)
        out_fname = get_out_fname_twnc(fname, input_dir, output_dir)
        if out_fname is None:
            logger.error('\n[input filename incorrect form] file: \n{}'.format(fname))
        os.makedirs(os.path.dirname(out_fname), exist_ok=True)
        art_fname = get_art_fname_twnc(fname, input_dir, art_dir)
        add_bound(fname, art_fname, out_fname)


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

    # artikels = []
    # print(num_sents, num_alpinos)
    # if num_sents == num_alpinos, we can be sure that sentences are in same order
    # and no sentence is missing between two files
    if num_sents == num_alpinos:
        flag = compare_signs(conll_sents, arts_dict)
        if flag:
            artikels = add_bound_text(conll_sents, arts_dict)
            for idx, art in enumerate(artikels):
                dir, fname = out_fname.rsplit(os.sep, 1)
                name, ext = fname.split('.', 1)
                filename = "{}/{}_{}.{}".format(dir, name, idx, ext)
                with codecs.open(filename, 'w', 'latin-1') as outf:
                    outf.write(art)
            # text = '\n'.join(artikels)
            # os.makedirs(os.path.dirname(out_fname), exist_ok=True)
            # with codecs.open(out_fname, 'w', 'latin-1') as outf:
            #     outf.write(text)
        else :
            logger.error('\n[Sentence signature inconsistent] file: \n{}'.format(conll_fname))
    elif num_sents - num_alpinos == 1:
        conll_sents = conll_sents[1:]
        flag = compare_signs(conll_sents, arts_dict)
        if flag:
            artikels = add_bound_text(conll_sents, arts_dict)
            for idx, art in enumerate(artikels):
                dir, fname = out_fname.rsplit(os.sep, 1)
                name, ext = fname.split('.', 1)
                filename = "{}/{}_{}.{}".format(dir, name, idx, ext)
                with codecs.open(filename, 'w', 'latin-1') as outf:
                    outf.write(art)
            # text = '\n'.join(artikels)
            # os.makedirs(os.path.dirname(out_fname), exist_ok=True)
            # with codecs.open(out_fname, 'w', 'latin-1') as outf:
            #     outf.write(text)
            # logger.error('\n[Sentence num diff=1] file: \n{}'.format(conll_fname))
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
    conll_root = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-converted/"
    art_root = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-wpr-art"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/TwNC-bound"

    # check whether paths exist
    paths = [conll_root, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(conll_root)
    corppar = CorpusHandler(conll_root, output_dir, art_root, method_multi=add_bound_multi)
    corppar.run_multi()


if __name__ == '__main__':
    main()
    # test_add_bound()
