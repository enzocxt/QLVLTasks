import os
import codecs

from collections import defaultdict
# from corpconv2.Sentence import Sentence


import xml.etree.ElementTree as ET


total_lines = 0


class Sentence(object):

    @classmethod
    def find(cls, node, element):
        item = cls.find_rec(node, element)
        return item

    @classmethod
    def find_rec(cls, node, element):
        res = node.find(element)
        if res is None:
            for item in node:
                res = Sentence.find_rec(item, element)
        return res


def split_by_tagname(text, tagname):
    """
    split the xml text by tagname
    """
    tags = []
    start = '<{}>'.format(tagname)
    end = '</{}>'.format(tagname)
    ls, le = len(start), len(end)
    size = len(text)
    i = 0
    while True:
        idx_start = text.find(start, i)
        idx_end = text.find(end, idx_start)
        if idx_start < 0 or idx_end < 0:
            # tag not found
            break
        tags.append(text[idx_start:(idx_end + le)])
        i = idx_end + le
        if i >= size:
            break

    return tags


def find_by_tagname(text, tagname):
    start = '<{}>'.format(tagname)
    end = '</{}>'.format(tagname)
    ls, le = len(start), len(end)
    idx_start = text.find(start)
    idx_end = text.find(end)
    if idx_start < 0:
        # tag start not found
        return None
    if idx_end < 0:
        # tag end not found
        return None
    content = text[(idx_start + ls):idx_end]
    return content


def split(filename):

    with codecs.open(filename, 'r', encoding='latin-1') as inf:
        context = inf.read()
        # articles = context.split('</article>')
        # articles = [(art + '</article>').strip() for art in articles if len(art.strip()) > 0]
        articles = split_by_tagname(context, 'article')

    art_dict = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : defaultdict(list))))
    for art in articles:
        '''
        root = ET.fromstring(art)
        # topic = Sentence.find(root, 'topic')
        section = Sentence.find(root, 'section')
        edition = Sentence.find(root, 'edition')
        author = Sentence.find(root, 'author')
        # topic = topic.text
        section, edition, author = section.text, edition.text, author.text
        '''
        # check article
        if '<article>' not in art or '</article>' not in art:
            continue

        topic = find_by_tagname(art, 'topic')
        section = find_by_tagname(art, 'section')
        subsect = find_by_tagname(art, 'subsection')
        edition = find_by_tagname(art, 'edition')

        blank = 'blank'
        if topic is None or len(topic) == 0:
            topic = blank
        if section is None or len(section) == 0:
            section = blank
        if subsect is None or len(subsect) == 0:
            subsect = blank
        if edition is None or len(edition) == 0:
            edition = blank

        topi_dict = art_dict[topic]
        sect_dict = topi_dict[section]
        subs_dict = sect_dict[subsect]
        subs_dict[edition].append(art)

    '''
    for k1, d1 in art_dict.items():
        print('topic: ', k1)
        for k2, d2 in d1.items():
            print('\tsection: ', k2)
            for k3, d3 in d2.items():
                print('\t\tsubsection: ', k3)
                for k4, d4 in d3.items():
                    print('\t\t\tedition:', k4)
                    print('\t\t\t\t', len(d4))
    '''
    return art_dict


def write(filename, art_dict, coding):
    for topi, dtopi in art_dict.items():
        for sect, dsect in dtopi.items():
            for subs, dsubs in dsect.items():
                for edit, ledit in dsubs.items():
                    fname = get_fname(filename, topi, sect, subs, edit)
                    arts = '\n'.join(ledit)
                    with codecs.open(fname, 'w', coding) as outf:
                        outf.write(arts)


def get_fname(filename, topi, sect, subs, edit):
    folder, fname = os.path.split(os.path.abspath(filename))
    steps = [topi, sect, subs, edit]
    next_folder = folder
    for step in steps:
        next_folder = os.path.join(next_folder, step)
        if not os.path.exists(next_folder):
            os.makedirs(next_folder)
    fname = os.path.join(next_folder, fname)
    return fname


if __name__ == '__main__':
    data_path = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output_LeNC"
    folder = "{}/Belgium/2005/belang_van_limburg".format(data_path)

    '''
    filename = "{}/Belgium/2005/belang_van_limburg/belang_van_limburg_20051229_01.conll".format(data_path)
    art_dict = split(filename)
    write(filename, art_dict)
    filename = "{}/Belgium/2005/belang_van_limburg/belang_van_limburg_20051231_01.conll".format(data_path)
    art_dict = split(filename)
    write(filename, art_dict)
    filename = "{}/Belgium/2005/belang_van_limburg/belang_van_limburg_20051230_01.conll".format(data_path)
    art_dict = split(filename)
    write(filename, art_dict)
    '''
    for fname in os.listdir(folder):
        fname = os.path.join(folder, fname)
        if os.path.isfile(fname):
            art_dict = split(fname)
            write(fname, art_dict, 'latin-1')
