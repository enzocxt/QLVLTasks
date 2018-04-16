from __future__ import absolute_import


import os
import codecs
import logging
import re
import traceback

from xml.parsers.expat import ExpatError
from xml.dom.minidom import parseString, Node
from xml.sax.saxutils import escape, unescape, quoteattr

from .alpino2tabUtils import *


logger = logging.getLogger('[alpino2tab:LeNC]')
logger.setLevel(logging.INFO)

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
parent_dir = os.path.dirname(cur_dir)
log_fname = "{}/alpino2tab_LeNC.log".format(parent_dir)

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


def parse(input_fname, output_fname):
    try:
        with open(input_fname) as xmlstream:
            xml_version = xmlstream.readline()
            xmlstring = xmlstream.read()
            lines = xmlstring.strip().split('\n')
            i = 0
            while True:
                line = lines[i]
                if not line.startswith('<!') and not line.startswith('<?'):
                    break
                i += 1
            lines = lines[i+1:-1]
            xmlfile = '\n'.join(lines)
            articles = xmlfile.split('</xmlfile>')
            articles = [(s + '</xmlfile>').strip() for s in articles[:-1]]

            get_alpino_ds()

    except Exception as e:
        print(e)


def get_alpino_ds():
    pass


def get_tag(xml_line):
    inner = ''
    start = 0
    while start < len(xml_line):
        lt_idx = xml_line.find('<', start)
        gt_idx = xml_line.find('>', lt_idx)
        inner = xml_line[(lt_idx+1):gt_idx]
        start = gt_idx + 1
    return inner


def alpino2tab(input_fname, output_fname):
    fname = input_fname.split(os.sep)[-1]
    try:
        with codecs.open(input_fname, 'r', options_dict['encoding']) as xmlstream,\
             codecs.open(output_fname, 'w', options_dict['encoding']) as tabstream:
            xml_version = xmlstream.readline().strip()    # xml version
            doctype = xmlstream.readline()
            conv_version = xmlstream.readline()
            # xml_version = ''.join([xml_version, doctype, conv_version])
            _reffile = xmlstream.readline()

            xmlstring = xmlstream.read()
            regex = r'&(?!lt;|gt;|amp;|apos;|quot;)'
            xmlstring = re.sub(regex, '&amp;', xmlstring)
            articles = split_by_tagname(xmlstring, 'xmlfile')
            articles = [xml_version + art for art in articles]

            for art in articles:
                # if article cannot be parsed
                # record error and skip
                art = parse_string(art, fname)
                if art is False:
                    continue

                art = get_article(art, fname)

                tabstream.write('<article>\n')
                topic = ''
                if len(art.getElementsByTagName("topic")) != 0:
                    if art.getElementsByTagName("topic")[0].firstChild is not None:
                        topic = art.getElementsByTagName("topic")[0].firstChild.data
                section, subsection, edition, date = '', '', '', ''

                authors = []
                for aut in art.getElementsByTagName("author"):
                    if len(aut.getElementsByTagName("namefirst")) == 0:
                        firstname = ''
                    elif aut.getElementsByTagName("namefirst")[0].firstChild is None:
                        firstname = ''
                    elif len(aut.getElementsByTagName("namefirst")) != 0:
                        firstname = aut.getElementsByTagName("namefirst")[0].firstChild.data
                    else:  #
                        firstname = ''

                    if len(aut.getElementsByTagName("namelast")) == 0:
                        lastname = ''
                    elif aut.getElementsByTagName("namelast")[0].firstChild is None:
                        lastname = ''
                    elif len(aut.getElementsByTagName("namelast")) != 0:
                        lastname = aut.getElementsByTagName("namelast")[0].firstChild.data
                    else:  #
                        lastname = ''
                    authors += [firstname + lastname]
                authorname = '_'.join(a for a in authors)

                auttags = []
                authortagline = art.getElementsByTagName("authortagline")
                '''
                if len(authortagline) == 0:
                    authorsentence = ''
                elif authortagline[0].firstChild is None:
                    authorsentence = ''
                '''
                authorsentence = ''
                if len(authortagline) != 0 and authortagline[0].firstChild is not None:
                    # for auttag in art.getElementsByTagName("authortagline"):
                    for auttag in authortagline:
                        sentence = auttag.getElementsByTagName("sentence")
                        if len(sentence) != 0:
                            authorsentence = '_'.join(
                                [s.firstChild.data for s in sentence]
                            )
                        auttags += [authorsentence]
                auttagname = '_'.join([at for at in auttags])

                topic, section, subsection, edition, date, author = '', '', '', '', '', ''
                section_ele = art.getElementsByTagName('section')
                subsection_ele = art.getElementsByTagName('subsection')
                edition_ele = art.getElementsByTagName('edition')
                pubdate_ele = art.getElementsByTagName('id')[0].getAttribute('pubdate')
                date = ''
                if section_ele[0].firstChild is not None:
                    section = section_ele[0].firstChild.data
                if subsection_ele[0].firstChild is not None:
                    subsection = subsection_ele[0].firstChild.data
                if edition_ele[0].firstChild is not None:
                    edition_list = [ed.firstChild for ed in edition_ele]
                    edition_list = [ed.data for ed in edition_list if ed is not None]
                    edition = '_'.join(edition_list)
                if pubdate_ele is not None:
                    date = pubdate_ele[0:10]

                if authorname is not '':
                    author = authorname
                else:
                    author = auttagname
                output = "<topic>" + topic + "</topic>\n" + \
                         "<section>" + section + "</section>\n" + \
                         "<subsection>" + subsection + "</subsection>\n" + \
                         "<edition>" + edition + "</edition>\n" + \
                         "<date>" + date + "</date>\n" + \
                         "<author>" + author + "</author>\n"
                tabstream.write(output)

                alpinods = art.getElementsByTagName("alpino_ds")
                for tree in alpinods:
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
    if tree.getAttribute("parsed") != "1":
        return

    removeWhitespaceNodes(tree)
    topnode = topNode(tree)
    tokens = getTokens(tree)

    removeEmptyNodes(tree)

    if options.concat_mwu:
        concatMultiWordUnits(tree, tokens)

    substituteHeadForPhrase(topnode)

    index = {}
    createIndex(topnode, index)
    '''
    words = [e.getAttribute('word') for e in index.values()]
    if len(tokens) != len(words):
        # print(tokens)
        # print(words)
        tokens = concat_tokens(tokens, set(words))
        # print(tokens)
    '''

    reattachPunctuation(topnode, index)
    # tabstream.write('<sentence>\n')
    sent_str = writeOutput(index, tabstream)
    sent_str = "<sentence>\n{}\n</sentence>\n".format(sent_str)
    # tabstream.write('</sentence>\n')
    tabstream.write(sent_str)
    # tokens do not match words
    # the xml element may be parsed incorrectly
    # after process this tree, record this error in log
    # if len(tokens) != len(words):
    #    raise ValueError("Tokens in sentence do not match words in xml attributes!!!")


def convert_log(tree, tabstream, fname):
    try:
        convert(tree, tabstream)
    except NegativeHeadError as e:
        logger.error("\n[alpino2tab:convert_log()] input file: {}"
                     "\nNegativeHeadError: {}"
                     .format(fname, e))
    except KeyError:
        logger.error("\n[alpino2tab:convert_log()] input file: {}"
                     "\nKeyError: writeOutput() for sentence"
                     .format(fname))
    except Exception as e:
        # traceback.print_exc()
        logger.error("\n[alpino2tab:convert_log()] input file: {}"
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


def get_article(art, fname):
    try:
        # there is only one "<article.published...>" in "<xmlfile...>"
        art = art.getElementsByTagName("article.published")[0]
    except Exception as e:
        # if occurs with error, then no article in xmlfile element
        # then skip this article
        logger.error("\n[alpino2tab:get_article()] input file: {}"
                     "\nError: {}"
                     .format(fname, e))
    return art
