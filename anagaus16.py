from argparse import ArgumentParser
import os
import re
import csv


# import numpy as np
# from collections import defaultdict
# from pathlib import Path


def init():
    parser = ArgumentParser()
    parser.add_argument("dirname", help="Give name of directory with Gaussian output files")
    parser.add_argument("-v", help="Output to stdout, no csv-output, unless -o or -w specified", action="store_true")
    parser.add_argument("-w", help="Force writing of csv-file, even if -v option is enabled", action="store_true")
    parser.add_argument("-o", "--outfile", help="Give name of csv-file")
    # todo add options for: split name; fc/es/gs force; ...
    args = parser.parse_args()
    fileflag = False
    if args.dirname[0] in ('/', '~'):
        dirname = args.dirname
    else:
        dirname = os.getcwd() + '/' + args.dirname
    if dirname[-1] != '/':
        if os.path.isfile(dirname):
            fileflag = os.path.basename(dirname)
            dirname = os.path.dirname(dirname) + '/'
        else:
            dirname = dirname + '/'
    if args.outfile:
        if re.search("[.]csv$", args.outfile):
            csvname = str("".join(args.outfile.split('.')[:-1]))
        else:
            csvname = str(args.outfile)
    else:
        csvname = 'results'
    main(dirname, outname=csvname, onefile=fileflag)
    if args.v:
        with open(dirname + csvname + '.csv', 'r') as csvfile:
            [print(line.rstrip()) for line in csvfile.readlines()]
        if not args.w and not args.outfile:
            os.remove(dirname + csvname + '.csv')


def main(alldir, outname='results', onefile=None):
    files_all = os.listdir(alldir)
    files_all.sort()
    if onefile is not None:
        files_all = [onefile]

    def log1out(infile, outfile):
        name = infile.split('/')[-1].replace('.log', '')
        print(name)  # , filedict)
        filedict = start_ana(infile)
        row1 = [name, filedict['genprops']['o/f'], filedict['genprops']['time'], filedict['genprops']['imag']]
        if filedict['gsprops'] is not None:
            row1.append(filedict['gsprops']['gse'])
            row1.append(filedict['gsprops']['zpe'])
        elif filedict['esprops'] is not None:
            es = filedict['esprops']['es_opt']
            row1.append(filedict['esprops']['ese'])
            row1.append(filedict['esprops']['zpe'])
            row1.append(es)
            row1.append(filedict['esprops']['esdict'][es]['emmE-eV'])
            row1.append(filedict['esprops']['esdict'][es]['f'])
            [row1.append(k) for k in filedict['esprops']['esdict'][es]['ifcoefs']]
        outfile.writerow(row1)

    def logFCout(infile, outfile):
        name = infile.split('/')[-1].replace('.log', '')
        print(name)  # , filedict)
        filedict = start_ana(infile)
        outfile.writerow(
            [name, filedict['genprops']['o/f'], filedict['genprops']['time'], filedict['genprops']['imag']])
        maxes = len(filedict['esprops']['esdict'])
        for k in range(1, maxes + 1):
            rowk = [name + '+' + str(k), "", "", ""]
            if k == filedict['esprops']['es_opt']:
                [rowk.append(elem) for elem in [filedict['esprops']['ese'], filedict['esprops']['zpe'], "fc" + str(k)]]
            else:
                [rowk.append(elem) for elem in ["", "", "fc" + str(k)]]
            rowk.append(filedict['esprops']['esdict'][k]['emmE-eV'])
            rowk.append(filedict['esprops']['esdict'][k]['f'])
            [rowk.append(k) for k in filedict['esprops']['esdict'][k]['ifcoefs']]
            outfile.writerow(rowk)

    with open(alldir + outname + '.csv', 'w') as f:
        csvw = csv.writer(f)
        csvw.writerow(['name', 'o/f', 'time', 'imag', 'gse/ese', 'zpe', 'esopt', 'emmE-eV', 'f', 'ifcoefs'])
        for allvar in files_all:
            if re.search("[Ff][Cc].*[.]log", allvar):
                logFCout(alldir + allvar, csvw)
            elif re.search("[.]log", allvar):
                log1out(alldir + allvar, csvw)


def dhms2time(d, h, m, s):
    return float(d) * 86400 + float(h) * 3600 + float(m) * 60 + float(s)


def start_ana(totfile):
    # Todo imag=None vs =0 --> difference in 0 and not finished (probably already possible with flags)
    # possibly imag=0 if of=True and el=2
    filedic = {'gsprops': None, 'esprops': None, 'genprops': {'time': 0, 'o/f': '', 'imag': None}}
    with open(totfile, "r") as fl:
        of_flag = False
        oc_flag = 0
        el_flag = 0
        el_time = []
        es_opt = 0
        es_flag = False
        es_max = 0
        # imag_num = 0
        er_flag = False
        eslines = []
        linenumber = 0
        for line in fl.readlines():
            linenumber = linenumber + 1
            if re.search('^ (Grad){18}$', line) and not of_flag:
                of_flag = True
            if of_flag:
                if re.search('Optimization completed[.]', line):
                    oc_flag = oc_flag + 1
                imag_match = re.search(r"[*]{6} +([0-9]+) imaginary frequencies \(negative Signs\) [*]{6}", line)
                if imag_match is not None:
                    imag_num = int(imag_match.group(1))
                    filedic['genprops']['imag'] = imag_num
            if re.search('Elapsed', line):
                el_time.append(dhms2time(line.split()[2], line.split()[4], line.split()[6], line.split()[8]))
                filedic['genprops']['time'] = sum(el_time)
                el_flag = el_flag + 1
            if re.search('This state for optimization and[/]or second-order correction[.]', line):
                es_flag = True
            if re.search('^ Excited State +', line):
                eslines.append(linenumber)
                num = int(line.replace(':', '').split()[2])
                if es_opt < num and not es_flag:
                    es_opt = num
                if es_max <= num:
                    es_max = num
            if re.search('Error termination', line):
                er_flag = True
    if er_flag:
        print('    --> Warning: terminated with error, values are probably wrong!')
    if of_flag:
        if oc_flag < el_flag:
            print('    --> Warning: opt not converged!')
        if es_flag:
            filedic = es_ana(totfile, filedic, es_opt, es_max, eslines[-1 * es_max:])
        if not es_flag:
            filedic = gs_ana(totfile, filedic)
    if not of_flag:
        if es_flag:
            filedic = es_ana(totfile, filedic, es_opt, es_max, eslines[-1 * es_max:], of=False)

    filedic['genprops']['o/f'] = 'of=%s-oc=%s' % (of_flag, oc_flag)
    return filedic


def es_ana(totfile, dic, es_opt, es_max, linenums, of=True):
    zpe_corr, ese_sum = 0, 0
    esdict = {i: {'emmE-eV': 0, 'emmE-nm': 0, 'f': 0, 's^2': 0, 'ifcoefs': None} for i in range(1, es_max + 1)}
    with open(totfile, "r") as fl:
        ifs_flag = False
        for i, line in enumerate(fl):
            if i < linenums[0] - 1:
                continue
            if of:
                zpe_corr, ese_sum = sezpe(line, [zpe_corr, ese_sum])
            tde_match = re.search(r"^ Total Energy, E\(TD-HF/TD-DFT\) = +([0-9.-]+)", line)
            if tde_match is not None:
                tde = float(tde_match.group(1))
            es_match = re.search(r"^ Excited State +([0-9]+): +(\S+) +([0-9.-]+) eV +([0-9.-]+) nm +f=([0-9.-]+) "
                                 r"+<S\*\*2>=([0-9.-]+)", line)
            if ifs_flag:
                ifcoef_match = re.search(r" +([0-9]{1,3}) (->|<-) ([0-9]{1,3}) +([0-9.-]+)", line)
                if ifcoef_match is not None:
                    # print(ifcoef_match.group(1, 3, 4))
                    ifcoefslist = [int(ifcoef_match.group(1)), int(ifcoef_match.group(3)), float(ifcoef_match.group(4))]
                    [ifs_mat.append(k) for k in ifcoefslist]
                else:
                    esdict[es_num]['ifcoefs'] = ifs_mat
                    ifs_flag = False
            if es_match is not None:
                es_num = int(es_match.group(1))
                esdict[es_num]['emmE-eV'] = float(es_match.group(3))
                esdict[es_num]['emmE-nm'] = float(es_match.group(4))
                esdict[es_num]['f'] = float(es_match.group(5))
                esdict[es_num]['s^2'] = float(es_match.group(6))
                ifs_flag = True
                ifs_mat = []

    if round(float(tde + zpe_corr), 5) != round(ese_sum, 5):
        if of:
            print('huh?')
        else:
            ese_sum = tde
            zpe_corr = 'No Freq!'
    dic['esprops'] = {'ese': ese_sum, 'zpe': zpe_corr, 'es_opt': es_opt, 'esdict': esdict}
    return dic


def sezpe(line, old_vals):
    zpe_corr, se_sum = old_vals[0], old_vals[1]
    zpe_match = re.search(r"^ Zero-point correction= +([0-9.-]+)", line)
    se_match = re.search(r"^ Sum of electronic and zero-point Energies=[ ]+([0-9.-]+)", line)
    if zpe_match is not None:
        zpe_corr = float(zpe_match.group(1))
    if se_match is not None:
        se_sum = float(se_match.group(1))
    return zpe_corr, se_sum


def gs_ana(totfile, dic):
    zpe_corr, gse_sum = 0, 0
    with open(totfile, "r") as fl:
        for line in fl:
            zpe_corr, gse_sum = sezpe(line, [zpe_corr, gse_sum])
    dic['gsprops'] = {'gse': gse_sum, 'zpe': zpe_corr}
    return dic


# def tst():
    # main('/home/u0133458/Documents/Calc/testg16/')
    # main('/home/u0133458/Documents/Calc/bapr2021/5q_mecn/')
    # t_file = '/home/u0133458/Documents/Calc/testg16/132.log'
    # dic1 = start_ana(t_file)
    # print(dic1)
    # exit()
    # with open('/home/u0133458/Documents/Calc/testg16/114.log', "r") as fl:
    # endmatch = re.findall(r"(?:.|\n)*\n [-]{70}\n((?:.|\n)*)(?:\\{3}\n? ?|\\{2}\n \\|\\\n \\{2})@\n\n", fl.read(),
    #                       re.MULTILINE)
    # print(endmatch[0].replace('\n ', ''))
    # imag_match = re.search(r"NImag=(.{,3})\\{2}", endmatch[0].replace('\n ', ''))
    # print(imag_match.group(1))


if __name__ == '__main__':
    init()
