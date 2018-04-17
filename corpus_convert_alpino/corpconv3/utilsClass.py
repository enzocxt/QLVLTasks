from __future__ import absolute_import

import os
import sys
import codecs
import html
from collections import defaultdict

from .utils import write_file
from .alpino2tabUtils import split_by_tagname


class MetaData(object):
    def __init__(self, meta_file_list):
        if meta_file_list is None or len(meta_file_list) == 0:
            raise AttributeError("Must provide meta data file names!")
        self.meta_file_list = meta_file_list
        self.meta_dict = dict()

    def read_metadata(self):
        metaBE_fname = self.meta_file_list[0]
        metaNL_fname = self.meta_file_list[1]

        metaBE_dict = self.read_meta_BE(metaBE_fname)
        self.meta_dict.update(metaBE_dict)
        metaNL_dict = self.read_meta_NL(metaNL_fname)
        self.meta_dict.update(metaNL_dict)

        return self.meta_dict

    def read_meta_BE(self, filename):
        meta_dict = dict()
        with codecs.open(filename, 'r', encoding='latin1') as inf:
            _header = inf.readline()
            metadata = [line.strip().split('"')[1::2] for line in inf.readlines()]
            for data in metadata:
                file_id = data[0][:-9]
                date = ''.join(data[6].split('-'))
                meta_dict[file_id] = (data[5], date)
        return meta_dict

    def read_meta_NL(self, filename):
        meta_dict = dict()
        with codecs.open(filename, 'r', encoding='latin1') as inf:
            _header = inf.readline()
            metadata = [line.strip().split('"')[1::2] for line in inf.readlines()]
            for data in metadata:
                if data[1].startswith('WR-P'):
                    newspaper = 'unknown'
                else:
                    newspaper = data[1].split(': ')[1].replace(' ', '_').lower()
                file_id = data[0][:-9]
                date = ''.join(data[6].split('-'))
                meta_dict[file_id] = (newspaper, date)
        return meta_dict


class Parser(object):

    @classmethod
    def parse(cls, filename, output_dir, meta_dict):
        skip_set = {'t_of_memory', 'me_out', 'art_hoot(time_out)', 'art_hook(time_out)'}
        with codecs.open(filename, 'r', encoding='latin1') as inf:
            context = inf.read()
            # sentences = context.split('</pre>')
            # sentences = [(s + '</pre>').strip() for s in sentences]
            sentences = context.split('</sentence>')
            sentences = [(s + '</sentence>').strip() for s in sentences]
            cur_file_id = ''
            cur_file = []
            for s in sentences:
                file_id = ''
                '''
                root = ET.fromstring(s.encode('latin1'))
                item = Sentence.find(root, 'file-id')
                if item is not None and item.text is not None:
                    file_id = item.text
                '''
                for line in s.split('\n'):
                    if line.strip().startswith('<file-id>'):
                        first = '<file-id>'
                        end = '</file-id>'
                        startidx = line.index(first) + len(first)
                        endidx = line.index(end, startidx)
                        file_id = line[startidx:endidx]
                        break

                if file_id == '' or file_id in skip_set:
                    continue
                if cur_file_id == '':   # first time
                    cur_file_id = file_id
                    cur_file.append(s)
                elif cur_file_id != file_id:  # meets a new file and output the previous one
                    cur_fname = FilenameGetter.get_output_fname_SoNaR(cur_file_id, output_dir, meta_dict)
                    context = '\n'.join(cur_file)
                    write_file(cur_fname, context)
                    cur_file_id = file_id
                    cur_file = [s]
                else:
                    cur_file.append(s)

    @classmethod
    def split_SoNaR(cls, filename, output_dir, meta_dict):
        skip_set = {'t_of_memory', 'me_out', 'art_hoot(time_out)', 'art_hook(time_out)', 'art_hook'}

        with codecs.open(filename, 'r', encoding='latin1') as inf:
            context = inf.read()
            sentences = split_by_tagname(context, 'sentence')

        cur_file_id = ''
        cur_file = []
        for s in sentences:
            file_id = ''
            for line in s.split('\n'):
                if line.strip().startswith('<file-id>'):
                    first = '<file-id>'
                    end = '</file-id>'
                    startidx = line.index(first)
                    endidx = line.index(end, startidx)
                    file_id = line[(startidx + len(first)):endidx]
                    break

            if file_id == '' or file_id in skip_set:
                continue
            if cur_file_id == '':   # first time
                cur_file_id = file_id
                cur_file.append(s)
            elif cur_file_id != file_id:  # meets a new file and output the previous one
                cur_fname = FilenameGetter.get_output_fname_SoNaR(cur_file_id, output_dir, meta_dict)
                context = '\n'.join(cur_file)
                write_file(cur_fname, context)
                cur_file_id = file_id
                cur_file = [s]
            else:
                cur_file.append(s)

    @classmethod
    def split_LeNC(cls, filename, output_dir):
        encoding = 'latin-1'
        with codecs.open(filename, 'r', encoding) as inf:
            context = inf.read()
            articles = split_by_tagname(context, 'article')

        art_dict = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : defaultdict(list))))
        for art in articles:
            cls.split_article(art, art_dict)

        fname = filename.split(os.sep)[-1]
        out_fname = FilenameGetter.get_output_fname_LeNC(fname, output_dir)
        for topi, dtopi in art_dict.items():
            for sect, dsect in dtopi.items():
                for subs, dsubs in dsect.items():
                    for edit, ledit in dsubs.items():
                        # check length of edition
                        if len(edit) > 21 and '_' in edit:
                            edits = edit.split('_')
                            edit_short = [e[0] if len(e) > 0 else '' for e in edits]
                            # in file DS_20050319_01.alpino.xml
                            # there is an article with incorrect editions
                            # the number of editions in it is too large
                            if len(edit_short) > 50:
                                edit_short = edit_short[:50]
                            edit_short = ''.join(edit_short)
                            fname = cls.get_fname(out_fname, topi, sect, subs, edit_short, encoding=encoding)
                            arts = '\n'.join(ledit)
                            with codecs.open(fname, 'w', encoding) as outf:
                                outf.write(arts)
                            edit_meta_fname = os.path.join(os.path.dirname(fname), 'edition_meta.txt')
                            with codecs.open(edit_meta_fname, 'w', encoding) as outf:
                                outf.write(edit)
                        else:
                            fname = cls.get_fname(out_fname, topi, sect, subs, edit)
                            arts = '\n'.join(ledit)
                            with codecs.open(fname, 'w', encoding) as outf:
                                outf.write(arts)

    @classmethod
    def split_article(cls, art, art_dict):
        topic = cls.find_by_tagname(art, 'topic')
        section = cls.find_by_tagname(art, 'section')
        subsect = cls.find_by_tagname(art, 'subsection')
        edition = cls.find_by_tagname(art, 'edition')

        if topic is None or len(topic) == 0:
            topic = 'default_topic'
        if section is None or len(section) == 0:
            section = 'default_section'
        if subsect is None or len(subsect) == 0:
            subsect = 'default_subsection'
        if edition is None or len(edition) == 0:
            edition = 'default_edition'

        topi_dict = art_dict[topic]
        sect_dict = topi_dict[section]
        subs_dict = sect_dict[subsect]
        subs_dict[edition].append(art)

    @staticmethod
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

    @staticmethod
    def get_fname(filename, topi, sect, subs, edit, encoding='utf-8'):
        folder, fname = os.path.split(os.path.abspath(filename))
        steps = [topi, sect, subs, edit]
        next_folder = folder
        for step in steps:
            next_folder = os.path.join(next_folder, step)
            next_folder = html.unescape(next_folder)
            # next_folder_str = next_folder.encode(encoding)  # encode file path
            if not os.path.exists(next_folder):
                try:
                    os.makedirs(next_folder)
                except OSError as e:
                    if e.errno != os.errno.EEXIST:
                        raise e
        fname = os.path.join(next_folder, fname)
        return fname


class FilenameGetter(object):
    _meta_data = {
        'ad': 'algemeen_dagblad',
        'nrc': 'nrc_handelsblad',
        'trouw': 'trouw',
        'parool': 'parool',
        'volkskrant': 'volkskrant',
        'vk': 'volkskrant',
        'DS': 'de_standaard',
        'BL': 'belang_van_limburg',
        'LN': 'het_laatste_nieuws',
        'DT': 'de_tijd',
        'NB': 'het_nieuwsblad',
        'DM': 'de_morgen',
    }
    _bel_set = {
        'de_standaard', 'dm_magazine', 'de_morgen',
        'het_laatste_nieuws', 'het_nieuwsblad',
        'belang_van_limburg', 'de_tijd'
    }
    _ned_set = {
        'nrc_handelsblad', 'trouw', 'volkskrant',
        'algemeen_dagblad', 'parool', 'unknown'
    }
    @classmethod
    def get_output_fname_SoNaR(cls, file_id, output_dir, meta_dict):
        if file_id not in meta_dict:
            print("file id not in meta info: ***{}***".format(file_id))
        krant, datum = meta_dict.get(file_id, ('unknown', '00000000'))
        jaar = datum[:4]
        if krant in cls._ned_set:
            nation = 'Netherlands'
        elif krant in cls._bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        name = file_id.split('-')[-1]
        filename = "{output}/{nation}/{year}/{news}/{krant}_{datum}_{name}.conll".format(
                   output=output_dir, nation=nation, year=jaar, news=krant,
                   krant=krant, datum=datum, name=name)

        # recursively create directories if they do not exist
        folders = filename.split('/')
        for i in range(3, len(folders)):
            path = '/'.join(folders[:i])
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except OSError as exc:
                    # if exc.errno != errno.EEXIST:
                    #    raise
                    raise exc

        return filename

    @classmethod
    def get_output_fname_LeNC(cls, file_id, output_dir):
        # 'NB_20051229_01.alpino.xml'
        name = file_id.split('.')[0]
        krant, datum, id = name.split('_')
        krant = cls._meta_data.get(krant, 'unknown')
        jaar = datum[:4]

        if krant in cls._ned_set:
            nation = 'Netherlands'
        elif krant in cls._bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        ppath = "{outdir}/{nation}/{year}/{news}".format(
                 outdir=output_dir, nation=nation, year=jaar, news=krant)

        if sys.version_info[0] < 3.2:
            # recursively create directories if they do not exist
            steps = [nation, jaar, krant]
            next_folder = output_dir
            for step in steps:
                next_folder = os.path.join(next_folder, step)
                if not os.path.exists(next_folder):
                    try:
                        os.makedirs(next_folder)
                    except OSError as e:
                        if e.errno != os.errno.EEXIST:
                            raise e
                    except Exception as e:
                        if not os.path.exists(next_folder):
                            raise e
        else:
            os.makedirs(ppath, exist_ok=True)

        filename = "{outdir}/{nation}/{year}/{news}/{krant}_{datum}_{id}.conll".format(
            outdir=output_dir, nation=nation, year=jaar, news=krant,
            krant=krant, datum=datum, id=id)
        return filename

    @classmethod
    def get_output_fname_TwNC(cls, file_id, output_dir):
        # 'nrc20040408.alpino.xml'
        # volkskrant20040227_up.artikelen-A.alpino.xml
        if '.alpino.xml' not in file_id:
            # must contain '.alpino.xml'
            raise ValueError("Incorrect file name.")
        name = file_id.replace('.alpino.xml', '')

        idx = 0
        for i, c in enumerate(name):
            if c.isdigit():
                idx = i
                break
        krant, datum = name[:idx], name[idx:]
        krant = cls._meta_data.get(krant, 'unknown')
        jaar = datum[:4]

        if krant in cls._ned_set:
            nation = 'Netherlands'
        elif krant in cls._bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        ppath = "{outdir}/{nation}/{year}/{news}".format(
                 outdir=output_dir, nation=nation, year=jaar, news=krant)

        if sys.version_info[0] < 3.2:
            # recursively create directories if they do not exist
            steps = [nation, jaar, krant]
            next_folder = output_dir
            for step in steps:
                next_folder = os.path.join(next_folder, step)
                if not os.path.exists(next_folder):
                    try:
                        os.makedirs(next_folder)
                    except OSError as e:
                        if e.errno != os.errno.EEXIST:
                            raise e
                    except Exception as e:
                        if not os.path.exists(next_folder):
                            raise e
        else:
            os.makedirs(ppath, exist_ok=True)

        filename = "{ppath}/{krant}_{datum}.conll".format(
                    ppath=ppath, krant=krant, datum=datum)
        return filename
