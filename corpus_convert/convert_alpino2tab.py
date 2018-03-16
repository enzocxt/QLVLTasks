import os

from corpconv.utils import timeit, list_dir_tree
from corpconv.CorpusParser import CorpusParser


options = {
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


@timeit
def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"

    # check whether paths exist
    paths = [input_dir, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    command = "python alpino2tab-v2-TwNC.py -c -e'latin-1' -f -a -l -p -r -w"
    xml_fn = '/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn/1999/ad/ad19991229.alpino.xml'
    tab_fn = os.path.basename(xml_fn).replace('.xml', '.conll')
    with open(xml_fn) as xml_inf, codecs.open(tab_fn, 'w', options['encoding']) as tab_outf:
        convert(xml_inf, tab_outf)


if __name__ == '__main__':
    # main stuff

    usage = \
    """
        %prog [options] FILES
    
    purpose:
        converts dependency trees in Alpino XML format to tabular format
    
    args:
        FILES              dependency trees in Alpino XML format
    """

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

