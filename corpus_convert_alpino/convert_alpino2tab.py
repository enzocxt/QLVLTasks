import os

from corpconv3.utils import timeit, list_dir_tree
from corpconv3.baseHandler import CorpusHandler


''' Method calling procedure
main_TwNC()
=> new CorpusParser('TwNC', input_dir, output_dir) -> corppar
   corppar.run_multi()
=> TwNCConverterMulti.convert_multi(input_dir, io_paths, meta_dict)
=> call_multi('TwNC', input_root, io_paths, files)
=> alpino2tab_multi('TwNC', files, io_paths)
'''

@timeit
def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output"
    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/twnc_unknownerr_files"
    # output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/twnc_unknownerr_files"

    # check whether paths exist
    paths = [input_dir, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    corppar = CorpusHandler('TwNC', input_dir, output_dir)
    corppar.run_multi()


@timeit
def main_LeNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/LeNC-alpino"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output"
    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/error_files/lenc/lenc_spliterr_files"
    # output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/error_files/lenc/lenc_spliterr_files"

    # check whether paths exist
    paths = [input_dir, output_dir]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    corppar = CorpusHandler('LeNC', input_dir, output_dir)
    corppar.run_multi()


@timeit
def main_SoNaR():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/SoNaR_ccl"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/output"

    metaBE_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/WR-P-P-G_newspapers.lectinfo.bel.txt"
    metaNL_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/WR-P-P-G_newspapers.lectinfo.ned.txt"
    metadata_files = (metaBE_fname, metaNL_fname)

    # check whether paths exist
    paths = [input_dir, output_dir, metaBE_fname, metaNL_fname]
    for p in paths:
        if not os.path.exists(p):
            raise AttributeError("File or directory not exists: \n{}".format(p))

    list_dir_tree(input_dir)
    corppar = CorpusHandler('SoNaR', input_dir, output_dir, meta_files=metadata_files)
    corppar.run_multi()


if __name__ == '__main__':
    main_TwNC()
    main_LeNC()
    # main_SoNaR()
    # for i in range(10):
    #     main_TwNC()

