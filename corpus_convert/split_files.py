import os
import sys


def main(input_dir, output_dir, command):
    """
    :param input_dir: the input folder which includes all files you want to process
    :param output_dir: the output folder
                       it will keep the file structure of the input folder
    :param command:
    :return:
    """
    command = ''

    # get the output of command
    # output = os.popen("ls").read()


if __name__ == '__main__':
    input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert"
    main()
    output_filename = "{newspaper_name}_{date}.conllu"
