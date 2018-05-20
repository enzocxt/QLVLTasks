# -*- coding: utf-8 -*-

"""
This file splits LeNC conll files by articles
"""

import os
import sys
import codecs
import logging
from collections import OrderedDict

from artUtils import *

# logging settings
logger = logging.getLogger('[LeNC: split articles]')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-4s %(levelname)-4s %(message)s')

file_path = os.path.abspath(__file__)
cur_dir = os.path.dirname(file_path)
log_fname = "{}/alpino2tab_TwNC_split.log".format(cur_dir)
file_handler = logging.FileHandler(log_fname)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
std_form = logging.Formatter('')


def get_conll_fnames(path):
    """
    get all conll filenames in this path
    this path should be a newspaper folder
    then the filenames are all of this newspaper
    """
    fnames = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.conll'):
                fname = os.path.join(root, f)
                fnames.append(fname)
    return fnames


def get_fnames_date(fnames):
    fnames_dict = OrderedDict()
    for fname in fnames:
        path, name = fname.rsplit(os.sep, 1)
        idx = 0
        for i, c in enumerate(name):
            if c.isdigit():
                idx = i
                break
        date = name[idx:idx+8]
        if date not in fnames_dict:
            fnames_dict[date] = list()
        fnames_dict[date].append(fname)
    return fnames_dict


def process_fnames(date, fnames, input_dir, io_paths, indent=''):
    input_root, output_root = io_paths
    # input_root: ".../output-LeNC"
    # input_dir: ".../output-LeNC/Belgium/2001/belang_van_limburg"
    # output_root: ".../output-LeNC-split"
    tail = input_dir.replace(input_root, '').strip(os.sep)
    eles = tail.split(os.sep)
    if len(eles) != 3:
        print("Error")
        logger.error("\n[filename incorrect] file: \n{}".format(input_dir))
    country, year, news = tail.split(os.sep)
    output_dir = "{root}/{country}/{year}/{date}/{news}".format(
        root=output_root, country=country, year=year, date=date, news=news
    )
    index = 0
    fnames = tqdm(fnames, unit='file', desc='{}'.format(indent))
    for fname in fnames:
        os.makedirs(output_dir, exist_ok=True)
        num = split_file(fname, output_dir, index)
        index += num


def split_file(fname, output_dir, index):
    """
    the index passed here should be the index of the first article in this file
    """
    with codecs.open(fname, 'r', 'latin-1') as inf:
        text = inf.read().strip()
        articles = split_by_tagname(text, 'article')
    for i, art in enumerate(articles):
        name = fname.rsplit(os.sep, 1)
        if len(name) != 2:
            print("Error")
            logger.error("\n[filename incorrect] file: \n{}".format(fname))
        name = name[-1]
        name, ext = name.rsplit('.', 1)
        name = "{}_{}.{}".format(name, index+i, ext)
        filename = os.path.join(output_dir, name)
        with codecs.open(filename, 'w', 'latin-1') as outf:
            outf.write(art)

    # delete input file
    try:
        os.remove(fname)
    except Exception as e:
        logger.error("\n[remove failed] file: \n{}".format(fname))

    return len(articles)


class CorpusHandler(object):
    def __init__(
            self,
            input_dir,
            output_dir,
            method_multi=None
    ):
        """
        :param input_dir: the input folder which includes all files you want to process
        :param output_dir: the output folder
        :param method_multi: the method which will be executed parallel
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.method_multi = method_multi

    def run_multi(self):

        self.deliver_and_run()

    def deliver_and_run(self, pg_leave=True):
        """
        recursively go to every folder and divide files for parallel methods
        """
        input_root = self.input_dir
        countries = tqdm(sorted(os.listdir(input_root)), unit='country', desc='{}{}'.format(' ' * 2, input_root.split('/')[-1]), leave=pg_leave)
        for country in countries:
            count_dir = os.path.join(input_root, country)
            if os.path.isfile(count_dir) or country != 'Belgium':
                continue
            years = tqdm(sorted(os.listdir(count_dir)), unit='year', desc='{}{}'.format(' ' * 4, count_dir.split('/')[-1]), leave=pg_leave)
            for year in years:
                year_dir = os.path.join(count_dir, year)
                if os.path.isfile(year_dir):
                    continue
                newss = tqdm(sorted(os.listdir(year_dir)), unit='news', desc='{}{}'.format(' ' * 6, year_dir.split('/')[-1]), leave=pg_leave)
                for news in newss:
                    news_dir = os.path.join(year_dir, news)
                    if os.path.isfile(news_dir):
                        continue
                    self.call_multi(news_dir, indent=' ' * 8)

    def call_multi(self, news_dir, indent=''):
        input_root = self.input_dir
        num_cores = mp.cpu_count() - 1

        fnames = get_conll_fnames(news_dir)
        fnames_dict = get_fnames_date(fnames)
        dates = sorted(fnames_dict.keys())
        num_dates = len(dates)
        data_group = [[] for _ in range(num_cores)]
        for i in range(num_dates):
            idx = i % num_cores
            data_group[idx].append(dates[i])

        io_paths = (input_root, self.output_dir)
        pool = mp.Pool(processes=num_cores)
        for i in range(num_cores):
            args = (data_group[i], fnames_dict, news_dir, io_paths,)
            kwds = {
                'indent': indent,
            }
            pool.apply_async(self.method_multi, args=args, kwds=kwds)
        pool.close()
        pool.join()


def split_lenc_multi(dates, fnames_dict, news_dir, io_paths, indent=''):
    subindent = indent + ' ' * 2
    pid = os.getpid()
    dates = tqdm(dates, unit='date', desc='{}proc({})'.format(indent, pid))
    for date in dates:
        fnames = fnames_dict[date]
        process_fnames(date, fnames, news_dir, io_paths, indent=subindent)


def main():
    conll_root = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/LeNC-topic"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output/LeNC-split"

    # check whether paths exist
    paths = [conll_root, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    # list_dir_tree(conll_root)
    corppar = CorpusHandler(conll_root, output_dir, method_multi=split_lenc_multi)
    corppar.run_multi()


if __name__ == '__main__':
    root_path = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output"
    '''
    path = "{}/Belgium/2001/belang_van_limburg".format(root_path)
    output_dir = "{}/LeNC-split".format(root_path)
    fnames = get_conll_fnames(path)
    fnames_dict = get_fnames_date(fnames)
    for date, fnames in fnames_dict.items():
        process_fnames(date, fnames, path, root_path, output_dir)
    '''
    main()
