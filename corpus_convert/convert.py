import os

from corpconv.utils import timeit, list_dir_tree
from corpconv.CorpusParser import CorpusParser


@timeit
def main_SoNaR():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/SoNaR_ccl"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-SoNaR.xq"
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"

    metaBE_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.bel.txt"
    metaNL_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.ned.txt"
    metadata_files = (metaBE_fname, metaNL_fname)

    # check whether paths exist
    paths = [input_dir, output_dir, xq_fname, saxon_jar, metaBE_fname, metaNL_fname]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('SoNaR', input_dir, output_dir, command=command)
    corppar = CorpusParser('SoNaR', input_dir, output_dir, command=command, meta_files=metadata_files)
    corppar.run_multi()


@timeit
def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-TwNC.xq"
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"

    # check whether paths exist
    paths = [input_dir, output_dir, xq_fname, saxon_jar]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('TwNC', input_dir, output_dir, command=command)
    corppar = CorpusParser('TwNC', input_dir, output_dir, command=command)
    corppar.run_multi()


@timeit
def main_LeNC():
    # modify the following paths if needed
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/LeNC-alpino"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    dtd_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/data/LeNC/PublishedArticle.dtd"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-LeNC-final.xq"
    mode = "conll"
    saxon_jar = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/saxon9he/saxon9he.jar"

    # check whether paths exist
    paths = [input_dir, output_dir, dtd_fname, xq_fname, saxon_jar]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('LeNC', input_dir, output_dir, command=command, dtd_fname=dtd_fname)
    corppar = CorpusParser('LeNC', input_dir, output_dir, command=command, dtd_fname=dtd_fname)
    corppar.run_multi()


if __name__ == '__main__':
    output_filename = "{newspaper_name}_{date}.conllu"
    main_SoNaR()
