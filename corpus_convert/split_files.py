import os
import sys
import shutil
import codecs


def parse(filename, output_dir):
    meta_dict = file_metadata()
    with codecs.open(filename, 'r', encoding='latin1') as inf:
        context = inf.read()
        sentences = context.split('</pre>')
        sentences = [(s + '</pre>').strip() for s in sentences]
        cur_file_id = ''
        cur_file = []
        for s in sentences:
            file_id = ''
            for line in s.split('\n'):
                if line.strip().startswith('<file-id>'):
                    first = '<file-id>'
                    end = '</file-id>'
                    startidx = line.index(first) + len(first)
                    endidx = line.index(end, startidx)
                    file_id = line[startidx:endidx]
                    break

            if file_id == '':
                continue
            if cur_file_id == '':   # first time
                cur_file_id = file_id
                cur_file.append(s)
            elif cur_file_id != file_id:  # meets a new file and output the previous one
                cur_fname = get_output_fname(cur_file_id, output_dir, meta_dict)
                context = '\n'.join(cur_file)
                write_file(cur_fname, context)
                cur_file_id = file_id
                cur_file = [s]
            else:
                cur_file.append(s)


def file_metadata():
    metaBE_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.bel.txt"
    metaNL_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/WR-P-P-G_newspapers.lectinfo.ned.txt"

    meta_dict = dict()
    with codecs.open(metaBE_fname, 'r', encoding='latin1') as inf:
        _header = inf.readline()
        metadata = [line.strip().split('"')[1::2] for line in inf.readlines()]
        for data in metadata:
            file_id = data[0][:-9]
            date = ''.join(data[6].split('-'))
            meta_dict[file_id] = (data[5], date)

    with codecs.open(metaNL_fname, 'r', encoding='latin1') as inf:
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


def get_output_fname(file_id, output_dir, meta_dict):
    ned_set = {'nrc_handelsblad', 'trouw', 'volkskrant', 'unknown', 'algemeen_dagblad'}
    bel_set = {'de_standaard', 'dm_magazine', 'de_morgen'}

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


def write_file(filename, context):
    with codecs.open(filename, 'w', encoding='latin1') as outf:
        outf.write(context)


def fname_checked(filename, tmpdir):
    if os.path.isdir(filename) or filename.startswith('.'):
        return False

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


def main(input_dir, output_dir, command, dtd_fname=None):
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

    # create a tmp directory for xQuery
    tmpDIR_dir = '{}/tmpDIR'.format(output_dir)
    if os.path.exists(tmpDIR_dir):
        shutil.rmtree(tmpDIR_dir)
    os.makedirs(tmpDIR_dir)
    # create a tmp directory for intermediate output
    tmpOUT_dir = '{}/tmp'.format(output_dir)
    if os.path.exists(tmpOUT_dir):
        shutil.rmtree(tmpOUT_dir)
    os.makedirs(tmpOUT_dir)
    if dtd_fname is not None:
        cp_cmd = "cp {} {}".format(dtd_fname, tmpDIR_dir + '/')
        os.system(cp_cmd)

    files = os.listdir(input_dir)
    i = 0
    for f in files:
        fname = '{}/{}'.format(input_dir, f)
        input_fname = fname_checked(fname, tmpDIR_dir)
        if not input_fname:
            continue
        i += 1

        tmp_in_fname = input_fname.split('/')[-1]
        tmp_out_fname = '.'.join(tmp_in_fname.split('.')[:-1] + ['conllu'])
        output_fname = '{}/{}'.format(tmpOUT_dir, tmp_out_fname)

        cmd = "{} DIR={} -o:{}".format(command, tmpDIR_dir, output_fname)
        # print("excuting system command for {} file:\n  {}".format(i, cmd))
        os.system(cmd)
        # print("done")

        parse(output_fname, output_dir)

        # remove input file in tmpDIR_dir
        os.system("rm {}".format(input_fname))
        # remove output file in tmpOUT_dir
        os.system("rm {}".format(output_fname))

        if (i + 1) % 10 == 0:
            # print("converted {} files".format(i + 1))
            print ".",


if __name__ == '__main__':
    output_filename = "{newspaper_name}_{date}.conllu"

    corpus_name = 'TwNC'
    # input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert"
    input_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/data/{}".format(corpus_name)
    output_dir = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/output/{}".format(corpus_name)
    dtd_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/data/{}/PublishedArticle.dtd".format(corpus_name)
    xq_fname = "/home/enzocxt/Projects/QLVL/other_tasks/corpus_convert/universal_dependencies_2.0-{}.xq".format(corpus_name)
    mode = "conll"
    saxon_jar = "./saxon9he/saxon9he.jar"
    # if you can run the command without '-cp' parameter
    # use: command = "java net.sf.saxon.Query ..." directly
    command = "java -cp {} net.sf.saxon.Query "\
              "-q:{} MODE={}".format(saxon_jar, xq_fname, mode)
    # main(input_dir, output_dir, command, dtd_fname=dtd_fname)
    main(input_dir, output_dir, command)

