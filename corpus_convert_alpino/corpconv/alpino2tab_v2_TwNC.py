from __future__ import absolute_import

'''
Script for converting dependency trees in Alpino XML format to tabular
format (e.g. the MALT-Tab format).
'''

__author__ = 'Erwin Marsi <e.c.marsi@uvt.nl>'
__version__ = '$Id: alpino2tab.py,v 1.9 2006/01/13 10:24:35 erwin Exp $'


import os
import codecs
import logging

from xml.parsers.expat import ExpatError
from xml.dom.minidom import parseString, Node

from .alpino2tabUtils import *


logger = logging.getLogger('[alpino2tab:TwNC]')
logger.setLevel(logging.INFO)

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
parent_dir = os.path.dirname(cur_dir)
log_fname = "{}/alpino2tab_TwNC.log".format(parent_dir)

file_handler = logging.FileHandler(log_fname)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


options_dict = {
    'all_warns': True,
    'blanks': False,
    'concat_mwu': False,
    'encoding': 'latin-1',
    'file': True,
    'link_du': True,
    'mark_mwu_alpino': False,
    'projective': True,
    'root': True,
    'terminator': '',
    'word_count': True,
}


class Options(object):
    def __init__(self, options_dict):
        self.all_warns = options_dict['all_warns']
        self.blanks = options_dict['blanks']
        self.concat_mwu = options_dict['concat_mwu']
        self.encoding = options_dict['encoding']
        self.file = options_dict['file']
        self.link_du = options_dict['link_du']
        self.mark_mwu_alpino = options_dict['mark_mwu_alpino']
        self.projective = options_dict['projective']
        self.root = options_dict['root']
        self.terminator = options_dict['terminator']
        self.word_count = options_dict['word_count']


options = Options(options_dict)


def alpino2tab(input_fname, output_fname):
    fname = input_fname.split(os.sep)[-1]
    try:
        with open(input_fname) as xmlstream, codecs.open(output_fname, 'w', 'latin-1') as tabstream:
            xml_version = xmlstream.readline()    # xml version
            xmlstream.readline()    # <alpino-sentences>
            alpinods = xmlstream.read().split('</alpino_ds>')
            alpinods = [(xml_version + s + '</alpino_ds>').strip() for s in alpinods[:-1]]

            tabstream.write('<article>\n')
            for tree in alpinods:
                try:
                    assert tree.endswith('</alpino_ds>')
                except AssertionError:
                    logger.error("\ninput file: {}"
                                 "\nSentence xml does not start with '<alpino_ds':"
                                 .format(fname))
                    continue

                try:
                    tree = parseString(tree).documentElement
                except ExpatError:
                    logger.error("\ninput file: {}"
                                 "\nxml.parsers.expat.ExpatError: not well-formed (invalid token)"
                                 .format(fname))
                    continue
                except Exception, e:
                    logger.error("\ninput file: {}"
                                 "\nError: cannot parse xml sentence\n{}"
                                 .format(fname, e))
                    continue

                if tree.nodeType == Node.TEXT_NODE and tree.data.strip() == '':
                    continue

                try:
                    convert(tree, tabstream)
                except NegativeHeadError, e:
                    logger.error("\ninput file: {}"
                                 "\nNegativeHeadError: {}"
                                 .format(fname, e))
                except KeyError:
                    logger.error("\ninput file: {}"
                                 "\nKeyError: writeOutput() for sentence"
                                 .format(fname))
                except Exception, e:
                    logger.error("\ninput file: {}"
                                 "\nError: {}"
                                 .format(fname, e))
            tabstream.write('</article>')
    except IOError as e:
        logger.error("\ninput file: {}"
                     "\nOperation failed: {}"
                     .format(fname, e))


def convert_v2(xmlstream, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    dom = parseString(string.join(xmlstream.readlines()))
    removeWhitespaceNodes(dom.documentElement)
    alpinods = dom.documentElement.childNodes
    for tree in alpinods:
        convert(tree, tabstream)


def convert(tree, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    removeWhitespaceNodes(tree)
    topnode = topNode(tree)
    ss = tree.getElementsByTagName('sentence')
    sentence = ss[0].childNodes[0].data
    tokens = getTokens(tree)

    removeEmptyNodes(tree)

    if options.concat_mwu:
        concatMultiWordUnits(tree, tokens)

    substituteHeadForPhrase(topnode)

    index = {}
    createIndex(topnode, index)
    '''
    if sentence.startswith("De Surinaamse politicus"):
        print(sentence)
        nodes = index.values()
        print('\n'.join([n.toxml() for n in nodes]))
    '''

    reattachPunctuation(topnode, index)
    tabstream.write('<sentence>\n')
    writeOutputNew(tokens, index, tabstream)
    tabstream.write('</sentence>\n')
