import os
import codecs

from collections import defaultdict
from corpconv.Sentence import Sentence

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


total_lines = 0


def split(filename):
    with codecs.open(filename, 'r', encoding='latin1') as inf:
        context = inf.read()
        sentences = context.split('</pre>')
        sentences = [(s + '</pre>').strip() for s in sentences if len(s) > 0]

    sent_dict = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))
    article = []
    pre_section = None
    pre_edition = None
    pre_author = None

    for s in sentences:
        root = ET.fromstring(s)
        section = Sentence.find(root, 'section')
        edition = Sentence.find(root, 'edition')
        author = Sentence.find(root, 'author')
        section, edition, author = section.text, edition.text, author.text

        # check section
        sect_dict = sent_dict[section]
        edit_dict = sect_dict[edition]
        edit_dict[author].append(s)

    return sent_dict


if __name__ == '__main__':
    path = "/home/enzocxt/Projects/QLVL/other_tasks/output"

    for root, dirs, files in os.walk(path):
        for f in files:
            filename = '{}/{}'.format(root, f)
            sent_dict = split(filename)
            print(sent_dict.keys())
