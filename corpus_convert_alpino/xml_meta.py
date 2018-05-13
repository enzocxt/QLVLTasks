# -*- coding: utf-8 -*-

"""
This file compares the articles between original xml files and conll files
"""

import os
import sys
import codecs
import time
import logging
from collections import OrderedDict
from tqdm import tqdm

from artUtils import *

logger = logging.getLogger('[TwNC: compare articles]')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
log_fname = "{}/alpino2tab_TwNC_art.log".format(cur_dir)
file_handler = logging.FileHandler(log_fname)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
std_form = logging.Formatter('')


root_path = os.path.dirname(__file__)


def analyse_art_multi(fnames, io_paths, indent=''):
    input_dir, output_dir, xml_dir = io_paths

    pid = os.getpid()
    fnames = tqdm(fnames, unit='file', desc='{}proc({})'.format(indent, pid))
    for fname in fnames:
        out_fname = fname.replace(input_dir, output_dir)
        xml_fname = get_xml_fname(fname, input_dir, xml_dir)
        if os.path.exists(xml_fname):
            compare(fname, xml_fname)


def compare_arts(bound_fname, xml_fname):

    with codecs.open(bound_fname, 'r', encoding='latin-1') as inf:
        text = inf.read().strip()
        conll_arts = split_by_tagname(text, 'artikel')

    with codecs.open(xml_fname, 'r', encoding='latin-1') as inf:
        text = inf.read().strip()
        xml_arts = split_by_tagname(text, 'artikel')

    i, j = 0, 0
    diff = []
    while True:
        if i >= len(conll_arts):
            break
        if j >= len(xml_arts):
            break
        csign = get_sign_conll_last(conll_arts[i], 1)
        xsign = get_sign_xml_last(xml_arts[j])
        print(i, csign)
        print(j, xsign)
        if not xsign.startswith(csign):
            # xsign_1st_long = get_1st_long_sign_xml(xml_arts[j])
            # if csign not in xsign_1st_long:
            xsign_2nd = get_sign_xml_nth(xml_arts[j], n=2)
            print(j, xsign_2nd)
            if not xsign_2nd.startswith(csign):
                xsign_3rd = get_sign_xml_nth(xml_arts[j], n=3)
                print(j, xsign_3rd)
                if not xsign_3rd.startswith(csign):
                    diff.append(j)
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
        j += 1
        time.sleep(0.05)
    if j < len(xml_arts):
        for k in range(j, len(xml_arts)):
            diff.append(j)

    print("\ninput file: \n{}\nxml artikels: {}, conll artikels: {}\ndiff: {}"
          .format(bound_fname, len(xml_arts), len(conll_arts), str(diff)))
    if len(xml_arts) - len(conll_arts) != len(diff):
        logger.info("\ninput file: \n{}\nxml artikels: {}, conll artikels: {}\ndiff: {}"
                    .format(bound_fname, len(conll_arts), len(xml_arts), str(diff)))


def compare(bound_fname, xml_fname):

    with codecs.open(bound_fname, 'r', encoding='latin-1') as inf:
        text = inf.read().strip()
        conll_arts = split_by_tagname(text, 'artikel')
        conll_arts = [split_by_tagname(art, 'sentence')[0] for art in conll_arts]
    conll_signs = [get_sign_conll_last(art, 1) for art in conll_arts]

    with codecs.open(xml_fname, 'r', encoding='latin-1') as inf:
        text = inf.read().strip()
        xml_arts = split_by_tagname(text, 'artikel')
    xml_signs = [get_sign_xml_long(art) for art in xml_arts]

    i, j = 0, 0
    diff = []
    while True:
        if i >= len(conll_signs):
            break
        if j >= len(xml_signs):
            break
        csign = conll_signs[i]
        xsign = xml_signs[j]
        print(i, csign)
        print(j, xsign)
        if csign not in xsign:
            diff.append(j)
        else:
            i += 1
        j += 1
        time.sleep(0.05)
    if j < len(xml_signs):
        for k in range(j, len(xml_signs)):
            diff.append(j)

    print("\ninput file: \n{}\nxml artikels: {}, conll artikels: {}\ndiff: {}"
          .format(bound_fname, len(xml_arts), len(conll_arts), str(diff)))
    if len(xml_arts) - len(conll_arts) != len(diff):
        logger.info("\ninput file: \n{}\nxml artikels: {}, conll artikels: {}\ndiff: {}"
                    .format(bound_fname, len(conll_arts), len(xml_arts), str(diff)))


def main():
    conll_root = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/TwNC-bound"
    xml_root = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/TwNC-meta"

    # check whether paths exist
    paths = [conll_root, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(conll_root)
    corppar = CorpusHandler(conll_root, output_dir, xml_root, method_multi=analyse_art_multi)
    # corppar = CorpusHandler(conll_root, output_dir, xml_root)
    corppar.run_multi()


if __name__ == '__main__':
    root_path = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/test_data/test_bound/xml_conll"
    bound_fname = "{}/volkskrant_20001228.conll".format(root_path)
    xml_fname = "{}/volkskrant20001228.xml".format(root_path)
    # main()
    bound_path = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/TwNC-bound"
    bound_fname = "{}/2000/algemeen_dagblad/algemeen_dagblad_20001230.conll".format(bound_path)
    xml_path = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC"
    xml_fname = "{}/2000/20001230/ad20001230.xml".format(xml_path)
    compare(bound_fname, xml_fname)
