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
        with codecs.open(input_fname, 'r', options_dict['encoding']) as xmlstream,\
             codecs.open(output_fname, 'w', options_dict['encoding']) as tabstream:
            xml_version = xmlstream.readline()    # xml version
            xmlstream.readline()    # <alpino-sentences>
            context = xmlstream.read()
            alpinods = split_by_tagname(context, 'alpino_ds')
            alpinods = [xml_version + alp for alp in alpinods]

            tabstream.write('<article>\n')
            for tree in alpinods:
                tree = parse_string(tree, fname)
                if tree is False:
                    continue
                # skip empty nodes
                if tree.nodeType == Node.TEXT_NODE and tree.data.strip() == '':
                    continue
                convert_log(tree, tabstream, fname)

            tabstream.write('</article>')
    except IOError as e:
        logger.error("\ninput file: {}"
                     "\nOperation failed: {}"
                     .format(fname, e))
    except Exception as e:
        logger.error("\ninput file: {}"
                     "\nOperation failed: {}"
                     .format(fname, e))


def convert(tree, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    removeWhitespaceNodes(tree)
    topnode = topNode(tree)
    tokens = getTokens(tree)

    removeEmptyNodes(tree)

    if options.concat_mwu:
        concatMultiWordUnits(tree, tokens)

    substituteHeadForPhrase(topnode)

    index = {}
    createIndex(topnode, index)
    words = [e.getAttribute('word') for e in index.values()]
    # words = [''.join(w.split()) for w in words]
    if len(tokens) != len(words):
        tokens = concat_tokens(tokens, set(words))
        if len(tokens) != len(words):
            raise ValueError("Tokens in sentence do not match words in xml attributes!!!")

    reattachPunctuation(topnode, index)
    # tabstream.write('<sentence>\n')
    sent_str = writeOutputNew(tokens, index, tabstream)
    # tabstream.write('</sentence>\n')
    sent_str = '<sentence>\n{}\n</sentence>\n'.format(sent_str)
    tabstream.write(sent_str)


def convert_log(tree, tabstream, fname):
    try:
        convert(tree, tabstream)
    except NegativeHeadError as e:
        logger.error("\ninput file: {}"
                     "\nNegativeHeadError: {}"
                     .format(fname, e))
    except KeyError:
        logger.error("\ninput file: {}"
                     "\nKeyError: writeOutput() for sentence"
                     .format(fname))
    except Exception as e:
        logger.error("\ninput file: {}"
                     "\nError: {}"
                     .format(fname, e))


def parse_string(tree, fname):
    # if article cannot be parsed
    # record error and skip
    try:
        tree = parseString(tree).documentElement
    except ExpatError as e:
        logger.error("\n[alpino2tab:parse_string()] input file: {}"
                     "\nxml.parsers.expat.ExpatError: not well-formed (invalid token)"
                     .format(fname))
        return False
    except Exception as e:
        logger.error("\n[alpino2tab:parse_string()] input file: {}"
                     "\nError: cannot parse xml sentence\n{}"
                     .format(fname, e))
        return False

    return tree


def convert_v2(xmlstream, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    dom = parseString(string.join(xmlstream.readlines()))
    removeWhitespaceNodes(dom.documentElement)
    alpinods = dom.documentElement.childNodes
    for tree in alpinods:
        convert(tree, tabstream)
