import os
import time
import html
import functools
import multiprocessing as mp
from tqdm import tqdm


class CorpusHandler(object):
    def __init__(
            self,
            input_dir,
            output_dir,
            xml_dir,
            method_multi=None
    ):
        """
        :param input_dir: the input folder which includes all files you want to process
        :param output_dir: the output folder
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.xml_dir = xml_dir
        self.method_multi = method_multi

    def run_multi(self):

        self.deliver_and_run(self.input_dir)

    def deliver_and_run(self, cur_input_dir, pg_leave=True):
        """
        recursively go to every folder and divide files for parallel methods
        """
        input_root = self.input_dir
        level = cur_input_dir.replace(input_root, '').count(os.sep)
        indent = ' ' * 2 * level
        files = os.listdir(cur_input_dir)
        dirs, files = file_filter(cur_input_dir, files)

        # call multiprocessing function for files
        if len(files) > 0:
            self.call_multi(cur_input_dir, files)

        # recursively call self for dirs
        dirs = tqdm(sorted(dirs), unit='dir', desc='{}{}'.format(indent, cur_input_dir.split('/')[-1]), leave=pg_leave)
        for d in dirs:
            abs_dir = '{path}{sep}{dir}'.format(path=cur_input_dir, sep=os.sep, dir=d)
            self.deliver_and_run(abs_dir, pg_leave=pg_leave)

    def call_multi(self, input_dir, files):
        input_root = self.input_dir
        level = input_dir.replace(input_root, '').count(os.sep)
        subindent = ' ' * 2 * level

        num_cores = mp.cpu_count() - 1
        num_files = len(files)
        data_group = [[] for _ in range(num_cores)]
        for i in range(num_files):
            idx = i % num_cores
            abs_fname = '{path}{sep}{fname}'.format(path=input_dir, sep=os.sep, fname=files[i])
            data_group[idx].append(abs_fname)

        # for experiment, only keep one first file in every group
        # data_group = [g[:1] for g in data_group]

        io_paths = (input_root, self.output_dir, self.xml_dir)
        pool = mp.Pool(processes=num_cores)
        for i in range(num_cores):
            args = (data_group[i], io_paths,)
            kwds = {
                'indent': subindent,
            }
            pool.apply_async(self.method_multi, args=args, kwds=kwds)
        pool.close()
        pool.join()


def timeit(fn):
    @functools.wraps(fn)
    def timer(*args, **kwargs):
        ts = time.time()
        result = fn(*args, **kwargs)
        te = time.time()
        f = lambda arg : type(arg)
        time_info = "\n************************************" + \
                    "\nfunction    = {0}".format(fn.__name__) + \
                    "\n  arguments = {0} {1}".format([f(arg) for arg in args], kwargs) + \
                    "\n  time      = %.6f sec" % (te-ts) + \
                    "\n************************************\n"
        # logger.info(time_info)
        print(time_info)
        return result
    return timer


def list_dir_tree(rootpath):
    for root, dirs, files in sorted(os.walk(rootpath)):
        level = root.replace(rootpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        # subindent = ' ' * 2 * (level + 1)
        num_files = len(files)
        file_info = "{} files".format(num_files)
        dir_info = "{}{}/ ({})".format(indent, os.path.basename(root), file_info)
        print(dir_info)
        # logger.info(dir_info)
        # print "{}{}/".format(indent, os.path.basename(root))
    # logger.info('')


def file_filter(path, files):
    res_dirs, res_files = [], []
    for fname in files:
        prefix, ext = os.path.splitext(fname)
        if os.path.isdir('{}/{}'.format(path, fname)):
            res_dirs.append(fname)
        elif ext == '.conll':
            res_files.append(fname)
    return res_dirs, res_files


def get_xml_fname(conll_fname, conll_root, xml_root):
    news_dict = {
        'algemeen_dagblad': 'ad',
        'nrc_handelsblad': 'nrc',
        'trouw': 'trouw',
        'parool': 'parool',
        'volkskrant': 'volkskrant',
    }

    path, fname = conll_fname.rsplit(os.sep, 1)
    idx = 0
    for i, c in enumerate(fname):
        if c.isdigit():
            idx = i
            break
    news, date = fname[:idx-1], fname[idx:]
    if news not in news_dict:
        raise ValueError("No such newspaper!")
    fname = '{}{}'.format(news_dict[news], date.replace('conll', 'xml'))
    # "/home/qlvl-corp/TwNC/2000/20000103/ad20000103.xml"
    xml_fname = "{root}/{year}/{date}/{fname}".format(
                root=xml_root, year=date[:4], date=date[:8], fname=fname)
    return xml_fname


def split_by_tagname(text, tagname, close=False):
    """
    split the xml text by tagname
    :param close: if close is True, use '<tagname>'
    """
    tags = []
    if close:
        start = '<{}>'.format(tagname)
    else:
        start = '<{}'.format(tagname)
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


def get_sign_conll(conll_art, idx):
    sentences = split_by_tagname(conll_art, 'sentence')
    if len(sentences) == 0:
        raise ValueError("This conll article has no sentence!")
    # signature of an article is the trigram of the first sentence
    return get_sign_sentence(sentences[0], idx)


def get_sign_conll_last(conll_art, idx):
    sentences = split_by_tagname(conll_art, 'sentence')
    if len(sentences) == 0:
        raise ValueError("This conll article has no sentence!")
    # signature of an article is the trigram of the last sentence
    return get_sign_sentence_last(sentences[-1], idx)


def get_sign_sentence_last(sentence, idx):
    n = 21   # number of characters to compose signature
    lines = sentence.strip().split('\n')
    i = 0
    sign = []
    for j in range(len(lines) - 1, -1, -1):
        line = lines[j]
        eles = line.split('\t')
        if len(eles) <= 2:  # not a normal line
            continue
        word = eles[idx]
        for k in range(len(word) - 1, -1, -1):
            c = word[k]
            if c.isalpha():
                sign.append(c)
                i += 1
            if i == n:
                break
        if i == n:
            break
    sign.reverse()
    sign = ''.join(sign)
    return sign


def get_sign_sentence(sentence, idx):
    """
    # get the first n words of a sentence
    get the first n characters (only alphabetic) of a sentence
    :param sentence:
    :param idx: the word index
    :return:
    """
    n = 21   # number of characters to compose signature
    lines = sentence.strip().split('\n')
    i = 0
    sign = []
    for line in lines:
        eles = line.split('\t')
        if len(eles) <= 2:  # not a normal line
            continue
        word = eles[idx]
        for c in word:
            if c.isalpha():
                sign.append(c)
                i += 1
            if i == n:
                break
        if i == n:
            break
    sign = ''.join(sign)
    # if len(sign) < n, there are not enough words in this sentence
    # to compose a 21 characters signature
    return sign


def get_sign_xml_last(xml_art):
    paras = split_by_tagname(xml_art, 'p', close=True)
    title = split_by_tagname(xml_art, 'ti', close=True)
    # number of paras in <ti>...</ti>, normally should be 1
    num_title = len(title)

    # normal useful paras
    paras = paras[num_title:]
    if len(paras) == 0:
        return ''
    p_last = paras[-1]
    p_last = get_content(p_last, 'p')

    sign = []
    n = 21
    i = 0
    for j in range(len(p_last) - 1, -1, -1):
        c = p_last[j]
        if c.isalpha():
            sign.append(c)
            i += 1
        if i == n:
            break
    sign.reverse()  # sign[::-1]
    sign = ''.join(sign)
    return sign


def get_1st_long_sign_xml(xml_art):
    paras = split_by_tagname(xml_art, 'p', close=True)
    title = split_by_tagname(xml_art, 'ti', close=True)
    num_title = len(title)   # normally should be 1
    paras = paras[num_title:]
    if len(paras) == 0:
        return ''
    p_1st = paras[0]
    p_1st = get_content(p_1st, 'p')
    words = p_1st.split()
    words = [w.strip() for w in words]
    sign = ''.join(words)
    return sign


def get_sign_xml_nth(xml_art, n=1):
    paras = split_by_tagname(xml_art, 'p', close=True)
    title = split_by_tagname(xml_art, 'ti', close=True)
    num_title = len(title)   # normally should be 1
    paras = paras[num_title:]
    if len(paras) < n:
        return ''
    p_1st = paras[n-1]
    p_1st = get_content(p_1st, 'p')

    sign = []
    num = 21    # number of characters to compose signature
    i = 0
    for c in p_1st:
        if c.isalpha():
            sign.append(c)
            i += 1
        if i == num:
            break
    sign = ''.join(sign)
    return sign


def get_sign_xml_long(xml_art):
    paras = split_by_tagname(xml_art, 'p', close=True)
    title = split_by_tagname(xml_art, 'ti', close=True)
    num_title = len(title)  # normally should be 1
    paras = paras[num_title:]
    if len(paras) < 1:
        return ''
    le = split_by_tagname(xml_art, 'le', close=True)
    if len(le) == 0:
        return ''
    le = le[0]
    paras = split_by_tagname(le, 'p', close=True)
    paras = ''.join([get_content(p, 'p') for p in paras])

    sign = []
    for c in paras:
        if c.isalpha():
            sign.append(c)
    sign = ''.join(sign)
    return sign


def get_2nd_sign_xml(xml_art):
    paras = split_by_tagname(xml_art, 'p', close=True)
    title = split_by_tagname(xml_art, 'ti', close=True)
    num_title = len(title)   # normally should be 1
    paras = paras[num_title:]
    if len(paras) < 2:
        return ''
    p_1st = paras[1]
    p_1st = get_content(p_1st, 'p')
    words = p_1st.split()
    words = [w.strip() for w in words[:3]]
    sign = ''.join(words)
    return sign


def get_content(text, tagname):
    start = len(tagname) + 2
    end = text.find('</{}>'.format(tagname))
    return html.unescape(text[start:end])