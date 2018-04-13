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
            # alpinods = context.split('</alpino_ds>')
            # alpinods = [(xml_version + s + '</alpino_ds>').strip() for s in alpinods[:-1]]
            alpinods = split_by_tagname(context, 'alpino_ds')
            alpinods = [xml_version + alp for alp in alpinods]

            tabstream.write('<article>\n')
            for tree in alpinods:
                # if article cannot be parsed
                # record error and skip
                try:
                    tree = parseString(tree).documentElement
                except ExpatError as e:
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
    removeWhitespaceNodes(tree)
    topnode = topNode(tree)
    uncat_tokens = getTokens(tree)

    removeEmptyNodes(tree)

    if options.concat_mwu:
        concatMultiWordUnits(tree, uncat_tokens)

    substituteHeadForPhrase(topnode)

    index = {}
    createIndex(topnode, index)
    words = [e.getAttribute('word') for e in index.values()]
    # words = [''.join(w.split()) for w in words]
    words = set(words)
    cat_words = words - set(uncat_tokens)
    tokens = concat_tokens(uncat_tokens, cat_words)

    reattachPunctuation(topnode, index)
    # tabstream.write('<sentence>\n')
    sent_str = writeOutputNew(tokens, index, tabstream)
    # tabstream.write('</sentence>\n')
    sent_str = '<sentence>\n{}\n</sentence>\n'.format(sent_str)
    tabstream.write(sent_str)


def convert_v2(xmlstream, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    dom = parseString(string.join(xmlstream.readlines()))
    removeWhitespaceNodes(dom.documentElement)
    alpinods = dom.documentElement.childNodes
    for tree in alpinods:
        convert(tree, tabstream)


def concat_tokens(uncat_tokens, cat_words):
    tokens = []
    i = 0
    while i < len(uncat_tokens):
        tok = uncat_tokens[i]
        if tok not in cat_words:
            tokens.append(tok)
        else:
            flag = True
            for cw in cat_words:
                if not cw.startswith(tok):
                    continue
                ws = cw.split()
                for k in range(len(ws)):
                    if i+k >= len(uncat_tokens) or uncat_tokens[i+k] != ws[k]:
                        flag = False
                        break
                if flag:
                    cat_tok = ''.join(ws)
                    break
            if flag:
                tokens.append(cat_tok)
            else:
                raise ValueError("Tokens in sentence do not match words in xml attributes!!!")
        i += 1
    return tokens
