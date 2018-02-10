# from __future__ import absolute_import

from corpconv.utils import timeit, list_dir_tree
from corpconv.main import process, process_multi


'''
log_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/log.txt"
logging.basicConfig(level=logging.INFO,
                    filename=log_fname,
                    format='%(asctime)s %(name)-4s %(levelname)-4s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filemode='w')
                    
handler_console = 'console'
logger = logging.getLogger('logger')
# console_logger.setLevel(logging.INFO)
# console_logger.addHandler()

# create StreamHandler
console = logging.StreamHandler(stream=None)
console.setLevel(logging.INFO)
logger.addHandler(console)
# create FileHandler
log_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/log.txt"
file_handler = logging.FileHandler(log_fname, mode='w', encoding=None, delay=False)
logger.addHandler(file_handler)
'''


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

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('SoNaR', input_dir, output_dir, command=command)
    process_multi('SoNaR', input_dir, output_dir, command=command, meta_files=metadata_files)


@timeit
def main_TwNC():
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-TwNC.xq"
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('TwNC', input_dir, output_dir, command=command)
    process_multi('TwNC', input_dir, output_dir, command=command)


@timeit
def main_LeNC():
    # modify the following paths if needed
    input_dir = "/home/enzocxt/Projects/QLVL/corp/nl/LeNC-alpino"
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output"
    dtd_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/data/LeNC/PublishedArticle.dtd"
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-LeNC-final.xq"
    mode = "conll"
    saxon_jar = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/saxon9he/saxon9he.jar"

    list_dir_tree(input_dir)
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query " \
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # process('LeNC', input_dir, output_dir, command=command, dtd_fname=dtd_fname)
    process_multi('LeNC', input_dir, output_dir, command=command, dtd_fname=dtd_fname)


if __name__ == '__main__':
    output_filename = "{newspaper_name}_{date}.conllu"
    main_TwNC()
