from __future__ import absolute_import

import os
import codecs
from .utils import write_file


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
        skip_set = {'t_of_memory', 'me_out', 'art_hoot(time_out)'}
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
            print "file id not in meta info: {}".format(file_id)
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
                    if exc.errno != errno.EEXIST:
                        raise

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
        filename = "{outdir}/{nation}/{year}/{news}/{krant}_{datum}_{id}.conll".format(
            outdir=output_dir, nation=nation, year=jaar, news=krant,
            krant=krant, datum=datum, id=id)

        # recursively create directories if they do not exist
        folders = filename.split('/')
        for i in range(3, len(folders)):
            path = '/'.join(folders[:i])
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise

        return filename

    @classmethod
    def get_output_fname_TwNC(cls, file_id, output_dir):
        # 'nrc20040408.alpino.xml'
        name = file_id.split('.')[0]
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
        filename = "{outdir}/{nation}/{year}/{news}/{krant}_{datum}.conll".format(
            outdir=output_dir, nation=nation, year=jaar, news=krant,
            krant=krant, datum=datum)

        # recursively create directories if they do not exist
        folders = filename.split('/')
        for i in range(3, len(folders)):
            path = '/'.join(folders[:i])
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise

        return filename
