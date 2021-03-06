'''
Script for converting dependency trees in Alpino XML format to tabular
format (e.g. the MALT-Tab format).
'''

__author__ = 'Erwin Marsi <e.c.marsi@uvt.nl>'
__version__ = '$Id: alpino2tab.py,v 1.9 2006/01/13 10:24:35 erwin Exp $'

import sys
import string
import os.path
import optparse
import codecs
from xml.dom.minidom import parseString, Node

from corpconv.utils import timeit, list_dir_tree
from corpconv.baseParser import CorpusParser


options_dict = {
    'all_warns': True,
    'blanks': False,
    'concat_mwu': True,
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


class ConversionError(Exception):
    pass


class NegativeHeadError(ConversionError):
    pass


class TwNCConverter(object):

    @classmethod
    def convert(cls, xmlstream, tabstream):
        """
        convert dependency tree in Alpino XML format to tabular format.
        """
        dom = parseString(string.join(xmlstream.readlines()))
        removeWhitespaceNodes(dom.documentElement)

        alpinods = dom.documentElement.childNodes

        tabstream.write('<article>\n')

        for tree in alpinods:
            topnode = topNode(tree)
            tokens = getTokens(tree)

            removeEmptyNodes(tree)

            if options.concat_mwu:
                concatMultiWordUnits(tree, tokens)

            substituteHeadForPhrase(topnode)

            index = {}
            createIndex(topnode, index)

            reattachPunctuation(topnode, index)
            tabstream.write('<sentence>\n')
            writeOutput(tokens, index, tabstream)
            tabstream.write('</sentence>\n')

        tabstream.write('</article>')

    @classmethod
    def topNode(cls, dom):
        """
        return the top node from the dependency tree
        """
        for child in dom.childNodes:
            if child.tagName == 'node':
                return child
        raise ValueError('Error: cannot find top node')

    @classmethod
    def getTokens(cls, dom):
        """
        return the tokens from the sentence
        """
        sentence = dom.getElementsByTagName("sentence")[0].childNodes[0].data
        return sentence.split()



def convert_LeNC(xmlstream, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    dom = parseString(string.join(xmlstream.readlines()))
    print(dom.documentElement)
    removeWhitespaceNodes(dom.documentElement)

    articles = dom.getElementsByTagName("article.published")

    for art in articles:
        tabstream.write('<article>\n')

        if len(art.getElementsByTagName("topic")) == 0:
            topic = ''
        elif art.getElementsByTagName("topic")[0].firstChild is None:
            topic = ''
        elif len(art.getElementsByTagName("topic")) != 0:
            topic = art.getElementsByTagName("topic")[0].firstChild.data

        if len(art.getElementsByTagName("section")) == 0 or art.getElementsByTagName("section")[0].firstChild is None:
            section = ''
        if len(art.getElementsByTagName("subsection")) == 0 or art.getElementsByTagName("subsection")[
            0].firstChild is None:
            subsection = ''
        if len(art.getElementsByTagName("edition")) == 0 or art.getElementsByTagName("edition")[0].firstChild is None:
            edition = ''
        if art.getElementsByTagName("id")[0].getAttribute("pubdate") is None:
            date = ''

        authors = []
        for aut in art.getElementsByTagName("author"):
            if len(aut.getElementsByTagName("namefirst")) == 0:
                firstname = ''
            elif aut.getElementsByTagName("namefirst")[0].firstChild is None:
                firstname = ''
            elif len(aut.getElementsByTagName("namefirst")) != 0:
                firstname = aut.getElementsByTagName("namefirst")[0].firstChild.data

            if len(aut.getElementsByTagName("namelast")) == 0:
                lastname = ''
            elif aut.getElementsByTagName("namelast")[0].firstChild is None:
                lastname = ''
            elif len(aut.getElementsByTagName("namelast")) != 0:
                lastname = aut.getElementsByTagName("namelast")[0].firstChild.data
            authors += [firstname + lastname]
        authorname = '_'.join(a for a in authors)

        auttags = []
        if len(art.getElementsByTagName("authortagline")) == 0:
            authorsentence = ''
        elif art.getElementsByTagName("authortagline")[0].firstChild is None:
            authorsentence = ''
        elif len(art.getElementsByTagName("authortagline")) != 0:
            for auttag in art.getElementsByTagName("authortagline"):
                if len(auttag.getElementsByTagName("sentence")) != 0:
                    authorsentence = '_'.join(s.firstChild.data for s in auttag.getElementsByTagName("sentence"))
                auttags += [authorsentence]
        auttagname = '_'.join(at for at in auttags)

        if art.getElementsByTagName("section")[0].firstChild is not None:
            section = art.getElementsByTagName("section")[0].firstChild.data
        if art.getElementsByTagName("subsection")[0].firstChild is not None:
            subsection = art.getElementsByTagName("subsection")[0].firstChild.data
        if art.getElementsByTagName("edition")[0].firstChild is not None:
            edition = '_'.join(ed.firstChild.data for ed in art.getElementsByTagName("edition"))
        if art.getElementsByTagName("id")[0].getAttribute("pubdate") is not None:
            date = art.getElementsByTagName("id")[0].getAttribute("pubdate")[0:10]

        tabstream.write('<topic>' + topic + '</topic>\n')
        tabstream.write('<section>' + section + '</section>\n')
        tabstream.write('<subsection>' + subsection + '</subsection>\n')
        tabstream.write('<edition>' + edition + '</edition>\n')
        tabstream.write('<date>' + date + '</date>\n')
        if authorname is not '':
            tabstream.write('<author>' + authorname + '</author>\n')
        else:
            tabstream.write('<author>' + auttagname + '</author>\n')

        alpinods = art.getElementsByTagName("alpino_ds")

        for tree in alpinods:
            if tree.getAttribute("parsed") == "1":

                topnode = topNode(tree)
                tokens = getTokens(tree)

                removeEmptyNodes(tree)

                if options.concat_mwu:
                    concatMultiWordUnits(tree, tokens)

                substituteHeadForPhrase(topnode)

                index = {}
                createIndex(topnode, index)

                reattachPunctuation(topnode, index)
                tabstream.write('<sentence>\n')
                writeOutput(tokens, index, tabstream)
                tabstream.write('</sentence>\n')

        tabstream.write('</article>\n')


def removeWhitespaceNodes(node):
    """
    remove the empty text nodes caused white space(indenting)
    in the input XML
    """
    # can be avoided by passing a DTD to the dom parser
    for child in list(node.childNodes):
        if child.nodeType == Node.TEXT_NODE and child.data.strip() == '':
            node.removeChild(child)
            child.unlink()
        else:
            removeWhitespaceNodes(child)


def removeEmptyNodes(node):
    """
    remove empty nodes (traces) and correct 'begin' and/or 'end'
    attributes of its parent
    """
    '''
    The problem is that if an initial (final) daughter is empty,
    then the 'start' ('end') attribute of the parent equals the 
    'start' ('end') attribute of the antecedent.
    Hence, when concatenating the tokens of a MWU, we get unintended results.
    The solution is to remove empty nodes first, and to correct the indices of
    its ancestors (that's the reason we traverse the tree bottom-up). 
    '''
    for child in list(node.childNodes):
        if not child.getAttribute('pos') and not child.getAttribute('cat'):
            node.removeChild(child)
            child.unlink()
        else:
            removeEmptyNodes(child)

    if node.hasChildNodes():
        node.setAttribute('begin', node.firstChild.getAttribute('begin'))
        node.setAttribute('end', node.lastChild.getAttribute('end'))


def reattachPunctuation(topnode, index):
    """
    detaches a punctuation symbol from the top node and reattaches it
    to the first non-punctuation token preceding it
    """
    '''
    Punctuation symbols are all attached to the top node. This is major
    source of unnecessary non-projectivity. Therefore punctuation symbols
    are reattached so that their head becomes the first non-punctuation token
    preceding. Punctuation symbols at the start of te sentence remain
    attached to the top node, as this poses no problem as far as
    # projectivity is concerned.
    '''
    for child in list(topnode.childNodes):
        #for (name, value) in child.attributes.items():
        #    print '    Attr -- Name: %s  Value: %s' % (name, value)
        if child.getAttribute('pos') == 'punct':
            # and not child.getAttribute('root') == '???':
            # Problem with file WR-P-P-C-0000000054.txt-42.xml
            # try the first preceding token
            i = int(child.getAttribute('begin')) - 1
            # search further to the left as long as were still on a punctuation token
            while i >= 0 and index[i].getAttribute('pos') == 'punct':
                i -= 1
            # unless we fell off the start of the sentence,
            # meaning this was sentence-initial punctuation,
            # reattach the child
            if i >= 0:
                child.setAttribute('rel', 'punct')
                topnode.removeChild(child)
                index[i].appendChild(child)


def topNode(dom):
    """
    return the top node from the dependency tree
    """
    for child in dom.childNodes:
        if child.tagName == 'node':
            return child
    raise ValueError('Error: cannot find top node')


def getTokens(dom):
    """
    return the tokens from the sentence
    """
    sentence = dom.getElementsByTagName("sentence")[0].childNodes[0].data
    return sentence.split()


def getFileId(dom):
    """
    return the fileid from the comments
    """
    comment = dom.getElementsByTagName("comment")[0].childNodes[0].data
    return comment[2:21]


def concatMultiWordUnits(dom, tokens):
    """
    removes the child nodes from multi word units,
    and concatenates the corresponding words
    """
    nodes = dom.getElementsByTagName('node')

    for node in nodes:
        if node.getAttribute('cat') == 'mwu':
            begin = int(node.getAttribute('begin'))
            end = int(node.getAttribute('end'))
            decr = end - begin - 1

            if options.mark_mwu_alpino:
                mwu = string.join(tokens[begin:end], '_')
                mwu = "[_@mwu_" + mwu + "_]"  # replace _ later
            else:
                mwu = string.join(tokens[begin:end], '_')

            # replace original tokens by concatenated tokens
            tokens[begin:end] = [mwu]

            pos = root = ''

            # remove children
            for child in list(node.childNodes):
                # also concat pos and root;
                # this assumes that the children are correctly ordered...
                # pos += child.getAttribute('pos') + '_'
                root += child.getAttribute('root') + '_'
                nodes.remove(child)
                node.removeChild(child)
                child.unlink()

            # node.setAttribute('pos', pos[:-1])
            node.setAttribute('pos', 'mwu')
            node.setAttribute('root', root[:-1])
            node.setAttribute('word', mwu)
            node.removeAttribute('cat')

            # now correct the tokens position indices for all subsequent nodes
            for node2 in nodes:
                # print node2.getAttribute('root')
                try:
                    begin2 = int(node2.getAttribute('begin'))
                    # print begin2, " ", begin, " ", node.getAttribute('root')
                    # print node2.getAttribute('root')
                    if begin2 > begin:
                        begin2 -= decr
                        if begin2 < 0:
                            raise NegativeHeadError
                        node2.setAttribute('begin', str(begin2))
                    end2 = int(node2.getAttribute('end'))
                    if end2 > begin:
                        end2 -= decr
                        if end2 < 0:
                            raise NegativeHeadError
                        node2.setAttribute('end', str(end2))
                except ValueError:
                    # empty nodes have no start & begin
                    pass


def substituteHeadForPhrase(parent):
    """
    replaces all phrasal nodes by their head nodes
    """
    # bottom-up traversal
    if parent.hasChildNodes():
        for child in list(parent.childNodes):
            # * remove empty childs to prevent empty heads
            # * if not child.getAttribute('pos') and not child.getAttribute('cat'):
            # *	parent.removeChild(child)
            # *	child.unlink()
            # * else:
            substituteHeadForPhrase(child)

        # don't bother to find a head for top
        if parent.getAttribute('cat') == 'top':
            return

        if parent.getAttribute('cat') == 'du' and not options.link_du:
            for child in parent.childNodes:
                # du's become linked to root
                child.setAttribute('rel', '--')
            return

        head = headChild(parent)

        parent.setAttribute('id', head.getAttribute('id'))
        parent.setAttribute('begin', head.getAttribute('begin'))
        parent.setAttribute('end', head.getAttribute('end'))
        parent.setAttribute('pos', head.getAttribute('pos'))
        parent.setAttribute('root', head.getAttribute('root'))
        parent.setAttribute('word', head.getAttribute('word'))
        parent.removeAttribute('cat')

        if head.hasChildNodes():
            # head child is a phrase such as a hd/mwu or nucl/smain,
            # so we move he head's children to the head's parent
            # before removing the child
            for headchild in list(head.childNodes):
                parent.appendChild(head.removeChild(headchild))

        parent.removeChild(head)


def headChild(parent):
    """
    returns the head of a phrasal node
    """
    for child in parent.childNodes:
        par_cat = parent.getAttribute('cat')
        child_rel = child.getAttribute('rel')

        # normal head, head of relative, wh clause, conjunction
        # or embedded clause ('cp','oti','ti', or 'ahi')
        if child_rel in ('hd', 'whd', 'rhd', 'crd', 'cmp'):
            return child

        # - du (discourse unit): prefer dlink, take nucl otherwise
        # (see below for dp)
        if par_cat == 'du' and child_rel == ('dlink', 'nucl'):
            return child

    else:
        '''
        Some rather arbitrary solution for exceptional cases:
        just take the first daughter as head. This occurs with:
        - mwu (multi word unit), unless --concat-mwu option
        - coordination without a conjunction (vg)
        - du (discourse unit) without nucl
        Note: stderr cannot handle unicode
        '''
        if par_cat not in ('mwu', 'conj') or options.all_warns:
            print >> sys.stderr, 'Warning: cannot find head child for parent:'
            print >> sys.stderr, '\t', parent.toprettyxml().split('\n')[0].encode('ascii', 'backslashreplace')
            print >> sys.stderr, 'default to first child:'
            print >> sys.stderr, '\t', parent.firstChild.toprettyxml().split('\n')[0].encode('ascii',
                                                                                             'backslashreplace')
        return parent.firstChild


def createIndex(parent, index=None):
    """
    return a dict mapping token positions to nodes
    """
    # since we're traversing top down,
    # don't bother testing if this is a leaf node
    if parent.getAttribute('word'):
        index[int(parent.getAttribute('begin'))] = parent

    for child in parent.childNodes:
        createIndex(child, index)


def writeOutput(tokens, index, tabstream=sys.stdout):
    """
    write output in tabular form
    """
    for i, word in enumerate(tokens):
        if options.word_count:
            if options.blanks:
                tabstream.write('%-4d' % (i + 1))
            else:
                tabstream.write('%d\t' % (i + 1))

        if options.blanks:
            tabstream.write('%-20s  ' % word)
        else:
            tabstream.write('%s\t' % word)

        if options.root:
            root = index[i].getAttribute('root').replace(' ', '_')
            if options.blanks:
                tabstream.write('%-20s  ' % root)
            else:
                tabstream.write('%s\t' % root)

        if options.blanks:
            tabstream.write('%-10s  ' % index[i].getAttribute('pos'))
        else:
            tabstream.write('%s\t' % index[i].getAttribute('pos'))

        rel = index[i].getAttribute('rel')

        if rel == '--':
            rel = 'ROOT'
            head = 0
        else:
            head = int(index[i].parentNode.getAttribute('begin')) + 1

        if options.blanks:
            tabstream.write('%-4d%-10s  ' % (head, rel))
        else:
            tabstream.write('%d\t%s' % (head, rel))

        if options.projective:
            if options.blanks:
                tabstream.write('  _  _')
            else:
                tabstream.write('\t_\t_')

        tabstream.write('\n')

    if options.terminator:
        tabstream.write('%s' % options.terminator)


def printIndices(dom, tokens):
    # a debug function
    for node in dom.getElementsByTagName('node'):
        if node.getAttribute('pos'):
            begin = int(node.getAttribute('begin'))
            end = int(node.getAttribute('end'))
            print '%2s %2s %8s %20s <==> %s' % (
                    node.getAttribute('begin'),
                    node.getAttribute('end'),
                    node.getAttribute('pos'),
                    node.getAttribute('word'),
                    tokens[begin:end])


def setup_parser():
    parser = optparse.OptionParser(usage, version=__version__)

    parser.add_option('-a', '--all-warnings',
                      dest='all_warns',
                      action='store_true',
                      default=False,
                      help='also show warnings about mwu and cnj')

    parser.add_option('-b', '--blanks',
                      dest='blanks',
                      action='store_true',
                      default=False,
                      help='use variable number of blanks as column separator (default is tab)')

    parser.add_option('-c', '--concat-mwu',
                      dest='concat_mwu',
                      action='store_true',
                      default=False,
                      help='concatenate the parts of a multi-word unit')

    parser.add_option('-e', '--encoding',
                      dest='encoding',
                      metavar='STRING',
                      default='utf-8',
                      help="output character encoding (default is utf-8)")

    parser.add_option('-f', '--file',
                      dest='file',
                      action='store_true',
                      default=False,
                      help='write output to file, replacing .xml by .tab')

    parser.add_option('-l', '--link-du',
                      dest='link_du',
                      action='store_true',
                      default=False,
                      help='force linking of discourse units')

    # added by Barbara, January 2010
    parser.add_option('-m', '--mark-mwu-alpino',
                      dest='mark_mwu_alpino',
                      action='store_true',
                      default=False,
                      help='mark mwu as [ @mwu ] instead of underscore (used by Alpino)')

    parser.add_option('-p', '--projective',
                      dest='projective',
                      action='store_true',
                      default=False,
                      help='include dummy columns for projective head and relation in output')

    parser.add_option('-r', '--root',
                      dest='root',
                      action='store_true',
                      default=False,
                      help='include root (lemma) column in output')

    parser.add_option('-t', '--terminator',
                      dest='terminator',
                      metavar='STRING',
                      default='',
                      help="terminator at end of table (default is '')")

    parser.add_option('-w', '--word-count',
                      dest='word_count',
                      action='store_true',
                      default=False,
                      help='include word count column in output')

    return parser


def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"

    # check whether paths exist
    paths = [input_dir, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    xml_fn = '/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn/1999/ad/ad19991229.alpino.xml'
    tab_fn = os.path.basename(xml_fn).replace('.xml', '.conll')
    with open(xml_fn) as xml_inf, codecs.open(tab_fn, 'w', options.encoding) as tab_outf:
        TwNCConverter.convert(xml_inf, tab_outf)


if __name__ == '__main__':
    # main stuff

    main_TwNC()

    usage = \
    """
        %prog [options] FILES
    
    purpose:
        converts dependency trees in Alpino XML format to tabular format
    
    args:
        FILES              dependency trees in Alpino XML format
    """

    '''
    # -c -e'latin-1' -f -a -l -p -r -w
    parser = setup_parser()
    (options, args) = parser.parse_args()

    # annoying: -t "\n" is stored by options parser as "\\n"
    if options.terminator:
        options.terminator = options.terminator.replace('\\n', '\n')

    if not args:
        sys.stderr.write('Error: incorrect number of arguments\n')
    else:
        for xml_fn in args:
            try:
                if options.file:
                    tab_fn = os.path.basename(xml_fn).replace('.xml', '.conll')
                    print >>sys.stderr, 'converting %s to %s' % (xml_fn, tab_fn)
                    convert(open(xml_fn), codecs.open(tab_fn, 'w', options.encoding))
                else:
                    print >>sys.stderr, 'converting', xml_fn
                    convert(open(xml_fn), codecs.EncodedFile(sys.stdout, options.encoding))
            except NegativeHeadError:
                print >>sys.stderr, 'ERROR: negative value for head. Skipping input file', xml_fn
    '''

