import os
from shutil import copy2
from collections import defaultdict


def analyze(filename):
    err_files = defaultdict(lambda : defaultdict(set))
    with open(filename) as inf:
        while True:
            line = inf.readline()
            if not line:
                break
            if line.startswith('input file'):
                fname = line.split(':')[-1].strip()
                err_line = inf.readline()
                if err_line is None:
                    break
                if ':' in err_line:
                    errcode, errmsg = err_line.split(':', 1)
                else:
                    errcode, errmsg = err_line.split(' ', 1)
                err_files[errcode]['message'].add(errmsg)
                err_files[errcode]['files'].add(fname)
    return err_files


if __name__ == '__main__':
    filename = "alpino2tab_TwNC.log.bak"
    # filename = "alpino2tab_SoNaR.log.bak"
    err_files = analyze(filename)

    print(err_files.keys())
    ''' KeyError files
    keyerr_files = err_files['KeyError']['files']
    # data_path = "/home/semmetrix/TwNC/TwNC-syn"
    # output_path = "/home/tao/other_tasks/corpus_convert_alpino/error_files"
    data_path = "/home/enzocxt/Projects/QLVL/corp/nl/TwNC-syn"
    output_path = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert_alpino/keyerr_files"
    for root, dirs, files in sorted(os.walk(data_path)):
        for fname in files:
            if fname in keyerr_files:
                # copy this file
                absfname = os.path.join(root, fname)
                outfname = os.path.join(output_path, fname)
                copy2(absfname, outfname)
    '''

    # index out of list
    print(err_files['Error']['message'])
    for fname in err_files['Error']['files']:
        print(fname)
    # ExpatError
    print(err_files['xml.parsers.expat.ExpatError']['message'])
    for fname in err_files['xml.parsers.expat.ExpatError']['files']:
        print(fname)
