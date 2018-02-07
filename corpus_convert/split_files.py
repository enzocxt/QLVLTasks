import os
import sys
import shutil
import codecs
import time

from tqdm import tqdm

import logging
import functools
import traceback

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        indent = ' ' * len(traceback.extract_stack())
        try:
            logging.debug('{0}entering {1}'.format(indent, fn.__name__))
            return fn(*args, **kwargs)
        except:
            logging.debug('{0}exception in {1}'.format(indent, fn.__name__))
            raise
        else:
            logging.debug('{0}leaving {1}'.format(indent, fn.__name__))

    return wrapper


def timeit(fn):
    @functools.wraps(fn)
    def timer(*args, **kwargs):
        ts = time.time()
        result = fn(*args, **kwargs)
        te = time.time()
        f = lambda arg : type(arg)
        print "\n************************************"
        print "function    = {0}".format(fn.__name__)
        print "  arguments = {0} {1}".format([f(arg) for arg in args], kwargs)
        # print "    return    = {0}".format(result)
        print "  time      = %.6f sec" % (te-ts)
        print "************************************\n"
        return result
    return timer


class Sentence(object):
    def __init__(self, xml_text):
        root = ET.fromstring(xml_text)
        sentence_tag = 'sentence'
        sentence_item = self.find_rec(root, sentence_tag)
        sentence = sentence_item.tail.strip()
        # list of items
        self.items = self.parse_sentence(sentence)

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

    def parse_sentence(self, sentence):
        # check every line in sentence
        # if line does not start with a digit number (current lemma id)
        # it should be the last line with '!'
        lines = sentence.split('\n')
        lines = filter(lambda x: x[0].isdigit(), map(lambda x: x.strip(), lines))
        return lines


class Parser(object):

    @classmethod
    @trace
    def parse(cls, filename, output_dir, meta_dict):
        skip_set = {'t_of_memory', 'me_out', 'art_hoot(time_out)'}
        with codecs.open(filename, 'r', encoding='latin1') as inf:
            context = inf.read()
            sentences = context.split('</pre>')
            sentences = [(s + '</pre>').strip() for s in sentences]
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


class MetaData(object):
    def __init__(self, meta_file_list=None):
        metaBE_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.bel.txt"
        metaNL_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.ned.txt"
        if meta_file_list is None or len(meta_file_list) == 0:
            self.meta_file_list = [metaBE_fname, metaNL_fname]
        else:
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
    @classmethod
    def get_output_fname_SoNaR(cls, file_id, output_dir, meta_dict):
        ned_set = {'nrc_handelsblad', 'trouw', 'volkskrant', 'unknown', 'algemeen_dagblad'}
        bel_set = {'de_standaard', 'dm_magazine', 'de_morgen', 'het_laatste_nieuws'}

        if file_id not in meta_dict:
            print "file id not in meta info: {}".format(file_id)
        krant, datum = meta_dict.get(file_id, ('unknown', '00000000'))
        jaar = datum[:4]
        if krant in ned_set:
            nation = 'Netherlands'
        elif krant in bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        name = file_id.split('-')[-1]
        filename = "{output}/{nation}/{year}/{news}/{prefix}_{name}.conll".format(
                   output=output_dir, nation=nation, year=jaar, news=krant,
                   prefix=krant+datum, name=name)

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
        ned_set = {'nrc_handelsblad', 'trouw', 'volkskrant', 'unknown', 'algemeen_dagblad', 'parool'}
        bel_set = {'de_standaard', 'dm_magazine', 'de_morgen', 'het_laatste_nieuws', 'het_nieuwsblad', 'belang_van_limburg',
                   'de_tijd'}

        # 'NB_20051229_01.alpino.xml'
        name = file_id.split('.')[0]
        krant, datum, id = name.split('_')
        krant = cls._meta_data.get(krant, 'unknown')
        jaar = datum[:4]

        if krant in ned_set:
            nation = 'Netherlands'
        elif krant in bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        filename = "{outdir}/{nation}/{year}/{news}/{krant}_{datum}_{id}.conll".format(
            outdir=output_dir, nation=nation, year=jaar, news=krant,
            krant=krant, datum=datum, id=id)

        return filename

    @classmethod
    def get_output_fname_TwNC(cls, file_id, output_dir):
        ned_set = {'nrc_handelsblad', 'trouw', 'volkskrant', 'unknown', 'algemeen_dagblad', 'parool'}
        bel_set = {'de_standaard', 'dm_magazine', 'de_morgen', 'het_laatste_nieuws', 'het_nieuwsblad', 'belang_van_limburg', 'de_tijd'}

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

        if krant in ned_set:
            nation = 'Netherlands'
        elif krant in bel_set:
            nation = 'Belgium'
        else:
            nation = 'Other'
        filename = "{outdir}/{nation}/{year}/{news}/{krant}_{datum}.conll".format(
            outdir=output_dir, nation=nation, year=jaar, news=krant,
            krant=krant, datum=datum)

        return filename


def write_file(filename, context):
    with codecs.open(filename, 'w', encoding='latin1') as outf:
        outf.write(context)


def check_fname(filename):
    suffix = filename.split('.')[-1]
    if filename.split('/')[-1].startswith('.'):
        return -1
    elif os.path.isdir(filename):
        return 0
    elif suffix in {'xml', 'gzip'}:
        return 1
    else:
        return -1


def copy_to_tmp(filename, tmpdir):
    suffix = filename.split('.')[-1]
    if suffix == 'xml':
        # copy current file into 'tmp' directory
        new_fname = '{}/{}'.format(tmpdir, filename.split('/')[-1])
        cp_cmd = "cp {} {}".format(filename, new_fname)
        os.system(cp_cmd)
        return new_fname
    elif suffix == 'gzip':
        new_fname = '{}/{}'.format(tmpdir, filename.split('/')[-1])
        cp_cmd = "cp {} {}".format(filename, new_fname)
        os.system(cp_cmd)
        xml_fname = new_fname[:-5]
        cmd = "gunzip -S .gzip {}".format(new_fname)
        os.system(cmd)
        return xml_fname
    else:
        return False


class Converter(object):
    def __init__(self, corpus_name=None):
        self.corpus_name = corpus_name

    def convert(self, *args, **kwargs):
        pass


class SoNaRConverter(Converter):
    def __init__(self, corpus_name=None):
        super(SoNaRConverter, self).__init__(corpus_name=corpus_name)

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, meta_dict=meta_dict, pg_leave=False)
                continue

            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
            output_fname = '{}/{}'.format(tmpOUT_dir, tmp_out_fname)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            # print cmd
            os.system(cmd)

            # split intermediate output into files
            Parser.parse(output_fname, output_dir, meta_dict)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # remove output file in tmpOUT_dir
            os.system("rm {}".format(output_fname))


class LeNCConverter(Converter):
    def __init__(self, corpus_name=None):
        super(LeNCConverter, self).__init__(corpus_name=corpus_name)

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, meta_dict=None, pg_leave=False)
                continue

            # in_filename has only filename without system path
            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            output_fname = FilenameGetter.get_output_fname_LeNC(tmp_in_fname, output_dir)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            os.system(cmd)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # as we don't have tmp output file for TwNC corpus
            # we do not need to remove output file in tmpOUT_dir


class TwNCConverter(Converter):
    def __init__(self, corpus_name=None):
        super(TwNCConverter, self).__init__(corpus_name=corpus_name)

    @classmethod
    def convert(cls, input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command='', meta_dict=None, pg_leave=True):
        depth = len(traceback.extract_stack()) - 3
        indent = '  ' * depth
        files = tqdm(os.listdir(input_dir), unit='file', desc='{}corpus'.format(indent), leave=pg_leave)

        for f in files:
            fname = '{}/{}'.format(input_dir, f)
            res = check_fname(fname)
            if res < 0:
                continue
            elif res == 0:  # it is a directory, recursively run convert()
                cls.convert(fname, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, pg_leave=False)
                continue

            # in_filename has only filename without system path
            input_fname = copy_to_tmp(fname, tmpDIR_dir)
            tmp_in_fname = input_fname.split('/')[-1]
            output_fname = FilenameGetter.get_output_fname_TwNC(tmp_in_fname, output_dir)

            # run xQuery command
            cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
            os.system(cmd)

            # remove input file in tmpDIR_dir
            os.system("rm {}".format(input_fname))
            # as we don't have tmp output file for TwNC corpus
            # we do not need to remove output file in tmpOUT_dir


@timeit
def process(corpus_name, input_dir, output_dir, command='', dtd_fname=None):
    """
    :param input_dir: the input folder which includes all files you want to process
    :param output_dir: the output folder
                       it will keep the file structure of the input folder
    :param command: xQuery command
    :return:
    """
    # create output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # create a tmp directory for xQuery's input (under output directory)
    tmpDIR_dir = '{}/tmpDIR'.format(output_dir)
    if os.path.exists(tmpDIR_dir):
        shutil.rmtree(tmpDIR_dir)
    os.makedirs(tmpDIR_dir)
    # create a tmp directory for intermediate output
    tmpOUT_dir = '{}/tmp'.format(output_dir)
    if os.path.exists(tmpOUT_dir):
        shutil.rmtree(tmpOUT_dir)
    os.makedirs(tmpOUT_dir)
    # if processing LeNC corpus, dtd file is needed
    if corpus_name == 'LeNC':
        if dtd_fname is None:
            raise AttributeError('Must provide dtd file!')
        else:
            cp_cmd = "cp {} {}".format(dtd_fname, tmpDIR_dir + '/')
            os.system(cp_cmd)

    mapper = {'SoNaR': SoNaRConverter,
              'LeNC': LeNCConverter,
              'TwNC': TwNCConverter,}

    # read meta data for corpus SoNaR
    meta_dict = None
    if corpus_name == 'SoNaR':
        md = MetaData()
        meta_dict = md.read_metadata()

    # recursively convert corpus files in input directory
    assert command != ''
    converter = mapper[corpus_name]
    converter.convert(input_dir, tmpDIR_dir, output_dir, tmpOUT_dir, command=command, meta_dict=meta_dict)

    # clean tmp folders
    os.system("rm -r {}".format(tmpDIR_dir))
    os.system("rm -r {}".format(tmpOUT_dir))


def main_SoNaR():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/SoNaR_ccl"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-SoNaR.xq"
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"

    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    process('SoNaR', input_dir, output_dir, command=command)


def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-TwNC.xq"
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"

    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    process('TwNC', input_dir, output_dir, command=command)


def main_LeNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/LeNC-alpino"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    dtd_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/data/LeNC/PublishedArticle.dtd"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-LeNC-final.xq"
    mode = "conll"
    saxon_jar = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/saxon9he/saxon9he.jar"

    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    process('LeNC', input_dir, output_dir, command, dtd_fname=dtd_fname)


if __name__ == '__main__':
    output_filename = "{newspaper_name}_{date}.conllu"
    main_SoNaR()
