from __future__ import absolute_import

'''
Script for converting dependency trees in Alpino XML format to tabular
format (e.g. the MALT-Tab format).
'''

__author__ = 'Erwin Marsi <e.c.marsi@uvt.nl>'
__version__ = '$Id: alpino2tab.py,v 1.9 2006/01/13 10:24:35 erwin Exp $'

import time
import sys
import string
import os.path
import optparse
import codecs
from xml.dom.minidom import parseString, Node

from .utils import timeit


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


def alpino2tab(input_fname, output_fname):
    try:
        with open(input_fname) as xmlstream, codecs.open(output_fname, 'w', 'latin-1') as tabstream:
            convert(xmlstream, tabstream)
    except IOError as e:
        print("Operation failed: {}".format(e.strerror))


def convert(xmlstream, tabstream):
    """
    convert dependency tree in Alpino XML format to tabular format.
    """
    # dom = parseString(string.join(xmlstream.readlines()))
    # read head
    xmlstream.readline()    # xml version
    xmlstream.readline()    # <treebank>
    alpinods = xmlstream.read().split('</alpino_ds>')
    alpinods = [(s + '</alpino_ds>').strip() for s in alpinods[:-1]]
    for tree in alpinods:
        try:
            assert tree.startswith('<alpino_ds')
        except AssertionError:
            print(tree)

    for tree in alpinods:
        tree = parseString(tree).documentElement
        global skip_nodes
        skip_nodes = get_ws_nodes(tree)
        skip_nodes = set(skip_nodes)
        # removeWhitespaceNodes(dom.documentElement)
        global empty_nodes
        empty_nodes = set()

        topnode = topNode(tree)
        tokens = getTokens(tree)
        comment = tree.getElementsByTagName("comment")[0].firstChild.nodeValue[2:21]

        # removeEmptyNodes(tree)
        empty_nodes.update(set(get_empty_nodes(tree)))

        if options.concat_mwu:
            concatMultiWordUnits(tree, tokens)

        substituteHeadForPhrase(topnode)

        index = {}
        createIndex(topnode, index)

        reattachPunctuation(topnode, index)
        tabstream.write('<sentence>\n')
        tabstream.write('<file-id>'+comment+'</file-id>\n')
        writeOutput(tokens, index, tabstream)
        tabstream.write('</sentence>\n')


def get_ws_nodes(root):
    children = []
    removeWhitespaceNodes(root, children)
    '''
    print("removing nodes...")
    for child in children:
        parent = child.parentNode
        parent.removeChild(child)
        child.unlink()
    '''
    return children


def removeWhitespaceNodes(node, children):
    """
    remove the empty text nodes caused white space(indenting)
    in the input XML  
    """
    '''
    # can be avoided by passing a DTD to the dom parser
    for child in list(node.childNodes):
        if child.nodeType == Node.TEXT_NODE and child.data.strip() == '':
            node.removeChild(child)
            child.unlink()
        else:
            removeWhitespaceNodes(child)
    '''

    for child in list(node.childNodes):
        # print(child.toxml())
        # time.sleep(2)
        if child.nodeType == Node.TEXT_NODE and child.data.strip() == '':
            children.append(child)
        else:
            removeWhitespaceNodes(child, children)


def get_empty_nodes(root):
    empty_nodes = []
    removeEmptyNodes(root, empty_nodes)
    return empty_nodes


def removeEmptyNodes(node, empty_nodes):
    """ 
    remove empty nodes (traces) and correct 'begin' and/or 'end'
    attributes of its parent
    """
    # The problem is that if an initial (final) daughter is empty,
    # then the 'start' ('end') attribute of the parent equals the 
    # 'start' ('end') attribute of the antecedent.
    # Hence, when concatenating the tokens of a MWU, we get unintended results.
    # The solution is to remove empty nodes first, and to correct the indices of
    # its ancestors (that's the reason we traverse the tree bottom-up).
    if not node.hasChildNodes():
        return

    child_nodes = list(node.childNodes)
    begin, end = -1, len(child_nodes)
    for i, child in enumerate(child_nodes):
        if child in skip_nodes:
            continue
        if not child.getAttribute('pos') and not child.getAttribute('cat'):
            empty_nodes.append(child)
        else:
            if begin < 0:
                begin = i
            end = i
            removeEmptyNodes(child, empty_nodes)

    begin_attr = child_nodes[begin].getAttribute('begin')
    end_attr = child_nodes[end].getAttribute('end')
    node.setAttribute('begin', begin_attr)
    node.setAttribute('end', end_attr)


def reattachPunctuation(topnode, index):
    """
    detaches a punctuation symbol from the top node and reattaches it 
    to the first non-punctation token preceding it
    """
    # Punctuation symbols are all attached to the top node. This is major
    # source of unnecessary non-projectivity. Therefore punctuation symbols
    # are reattached so that their head becomes the first non-punctation token
    # preceding. Punctuation symbols at the start of te sentence remain
    # attached to the top node, as this poses no problem as far as
    # projectivity is concerned.
    for child in list(topnode.childNodes):
        if child in skip_nodes or child in empty_nodes:
            continue
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
        if child in skip_nodes:
            continue
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
        if node in skip_nodes or node in empty_nodes:
            continue
        if node.getAttribute('cat') != 'mwu':
            continue
        begin = int(node.getAttribute('begin'))
        end = int(node.getAttribute('end'))
        decr = end - begin - 1

        if options.mark_mwu_alpino:
            mwu = string.join(tokens[begin:end], '_')
            mwu = "[_@mwu_" + mwu +"_]"     # replace _ later
        else:
            mwu = string.join(tokens[begin:end], '_')


        # replace original tokens by concatenated tokens
        tokens[begin:end] = [mwu]

        pos = root = ''

        # remove children
        for child in list(node.childNodes):
            if child in skip_nodes or child in empty_nodes:
                continue
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
            if node2 in skip_nodes or node2 in empty_nodes:
                continue
            #print node2.getAttribute('root')
            try:
                begin2 = int(node2.getAttribute('begin'))
                #print begin2, " ", begin, " ", node.getAttribute('root')
                #print node2.getAttribute('root')
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
    if not parent.hasChildNodes():
        return
    flag = True
    for node in parent.childNodes:
        if node not in skip_nodes and node not in empty_nodes:
            flag = False
    if flag:
        return

    # bottom-up traversal

    for child in list(parent.childNodes):
        '''
        * remove empty childs to prevent empty heads
        * if not child.getAttribute('pos') and not child.getAttribute('cat'):
        *	parent.removeChild(child)
        *	child.unlink()
        * else:
        '''
        substituteHeadForPhrase(child)

    # if the node is a whitespace or empty node
    if parent in skip_nodes or parent in empty_nodes:
        return
    # don't bother to find a head for top
    if parent.getAttribute('cat') == 'top':
        return
    if parent.getAttribute('cat') == 'du' and not options.link_du:
        for child in parent.childNodes:
            if child in skip_nodes or child in empty_nodes:
                continue
            # du's become linked to root
            child.setAttribute('rel', '--')
        return

    head = headChild(parent)
    attrs = ['id', 'begin', 'end', 'pos', 'root', 'word']
    for attr in attrs:
        parent.setAttribute(attr, head.getAttribute(attr))
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
        if child in skip_nodes or child in empty_nodes:
            continue
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

    '''
    Some rather arbitrary solution for exceptional cases:
    just take the first daughter as head. This occurs with:
    - mwu (multi word unit), unless --concat-mwu option
    - coordination without a conjunction (vg)
    - du (discourse unit) without nucl
    Note: stderr cannot handle unicode
    '''
    '''
    if par_cat not in ('mwu', 'conj') or options.all_warns:
        print >>sys.stderr, 'Warning: cannot find head child for parent:'
        print >>sys.stderr,  '\t', parent.toprettyxml().split('\n')[0].encode('ascii','backslashreplace')
        print >>sys.stderr, 'default to first child:'
        print >>sys.stderr, '\t', parent.firstChild.toprettyxml().split('\n')[0].encode('ascii','backslashreplace')
    '''
    # return parent.firstChild
    for child in parent.childNodes:
        if child not in skip_nodes and child not in empty_nodes:
            return child


def createIndex(parent, index=None):
    """
    return a dict mapping token positions to nodes 
    """
    # since we're traversing top down,
    # don't bother testing if this is a leaf node
    if parent in skip_nodes or parent in empty_nodes:
        return

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
            root = index[i].getAttribute('root').replace(' ','_')
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
        tabstream.write('%s' %  options.terminator)
    

def printIndices(dom, tokens):
    # a debug function
    for node in dom.getElementsByTagName('node'):
        if node.getAttribute('pos'):
            print('%2s %2s %8s %20s <==> %s' % ( node.getAttribute('begin'),
                                                 node.getAttribute('end'),
                                                 node.getAttribute('pos'),
                                                 node.getAttribute('word'),
                                                 tokens[int(node.getAttribute('begin')):int(node.getAttribute('end'))]))
            
    
'''
# main stuff    

usage = \
"""
    %prog [options] FILES

purpose:
    converts dependency trees in Alpino XML format to tabular format

args:
    FILES              dependency trees in Alpino XML format"""

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


(options, args) = parser.parse_args()


# annoying: -t "\n" is stored by options parser as "\\n"
if options.terminator:
    options.terminator = options.terminator.replace('\\n', '\n')

if not args:
    sys.stderr.write('Error: incorrect number of arguments\n')
else:
    for xmlfn in args:
        try:
            if options.file:
                tabfn = os.path.basename(xmlfn).replace('.xml','.conll')
                print >>sys.stderr, 'converting %s to %s' % (xmlfn, tabfn)	    
                convert(open(xmlfn), codecs.open(tabfn, 'w', options.encoding))
            else:
                print >>sys.stderr, 'converting', xmlfn	    
                convert(open(xmlfn), codecs.EncodedFile(sys.stdout, options.encoding))
        except NegativeHeadError:
            print >>sys.stderr, 'ERROR: negative value for head. Skipping input file', xmlfn

#options.word_count = True
#options.terminator = ''
#options.projective = True
#options.blanks = False
#options.root = True
#options.file = True
#options.encoding = 'utf-8'
#options.mark_mwu_alpino = False
#options.concat_mwu = True
#options.link_du = True
'''
