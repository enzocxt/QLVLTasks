import os
import sys
import shutil


def main(input_dir, output_dir, command):
    """
    :param input_dir: the input folder which includes all files you want to process
    :param output_dir: the output folder
                       it will keep the file structure of the input folder
    :param command:
    :return:
    """

    # get the output of command
    # output = os.popen("ls").read()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = os.listdir(input_dir)
    for f in files:
        if f.startswith('.'):
            continue
        fname = '{}/{}'.format(input_dir, f)
        if os.path.isdir(fname):
            continue
        tmpdir = '{}/tmp'.format(input_dir)
        # create a tmp directory for this file
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        # copy current file into this tmp directory
        cp_cmd = "cp {} {}".format(fname, tmpdir + '/' + f)
        os.system(cp_cmd)

        outf = '.'.join(f.split('.')[:-1] + ['conllu'])
        output_fname = "{}/{}".format(output_dir, outf)

        cmd = "{} DIR={} -o:{}".format(command, tmpdir, output_fname)
        print("excuting system command:\n  {}".format(cmd))
        os.system(cmd)
        print("done")


if __name__ == '__main__':
    output_filename = "{newspaper_name}_{date}.conllu"

    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert"
    input_dir = "/Users/enzo/Projects/QLVL/other_tasks/corpus_convert/SoNaR"
    output_dir = "/Users/enzo/Projects/QLVL/other_tasks/corpus_convert/output/SoNaR"
    xq_fname = "/Users/enzo/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-SoNaR.xq"
    mode = "conll"
    saxon_jar = "./SaxonHE9-8-0-7J/saxon9he.jar"
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query "\
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    main(input_dir, output_dir, command)
