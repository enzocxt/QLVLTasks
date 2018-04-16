from __future__ import absolute_import


import os
import logging
import codecs

from xml.parsers.expat import ExpatError
from xml.dom.minidom import parseString, Node

from .alpino2tabUtils import *


logger = logging.getLogger('[alpino2tab:SoNaR]')
logger.setLevel(logging.INFO)

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
parent_dir = os.path.dirname(cur_dir)
log_fname = "{}/alpino2tab_SoNaR.log".format(parent_dir)

file_handler = logging.FileHandler(log_fname)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


options_dict = {
    'all_warns': True,
    'blanks': False,
    'concat_mwu': False,
    'encoding': 'UTF-8',
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
            # alpinods = xmlstream.read().split('</alpino_ds>')
            # alpinods = [(xml_version + s + '</alpino_ds>').strip() for s in alpinods[:-1]]
            alpinods = split_by_tagname(context, 'alpino_ds')
            alpinods = [xml_version + alp for alp in alpinods]

            tabstream.write('<article>\n')
            for tree in alpinods:
                # if article cannot be parsed
                # record error and skip
                try:
                    tree = parseString(tree).documentElement
                except ExpatError:
                    logger.error("\ninput file: {}"
                                 "\nxml.parsers.expat.ExpatError: not well-formed (invalid token)"
                                 .format(fname))
                    continue
                except Exception as e:
                    logger.error("\ninput file: {}"
                                 "\nError: cannot parse xml sentence\n{}"
                                 .format(fname, e))
                    continue

                # skip empty nodes
                if tree.nodeType == Node.TEXT_NODE and tree.data.strip() == '':
                    continue

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
    # dom = parseString(string.join(xmlstream.readlines()))

    removeWhitespaceNodes(tree)
    topnode = topNode(tree)
    tokens = getTokens(tree)
    comment = tree.getElementsByTagName("comment")[0].firstChild.nodeValue[2:21]

    removeEmptyNodes(tree)

    if options.concat_mwu:
        concatMultiWordUnits(tree, tokens)

    substituteHeadForPhrase(topnode)

    index = {}
    createIndex(topnode, index)
    '''
    words = [e.getAttribute('word') for e in index.values()]
    if len(tokens) != len(words):
        tokens = concat_tokens(tokens, set(words))
        if len(tokens) == len(words):
            raise ValueError("Tokens in sentence do not match words in xml attributes!!!")
    '''

    reattachPunctuation(topnode, index)
    # tabstream.write('<sentence>\n')
    # tabstream.write('<file-id>'+comment+'</file-id>\n')
    sent_str = writeOutput(index, tabstream)
    sent_str = "<sentence>\n<file-id>{}</file-id>\n{}\n</sentence>\n".format(comment, sent_str)
    # tabstream.write(sent_str + '\n')
    # tabstream.write('</sentence>\n')
    tabstream.write(sent_str)
