#!python3
from argparse import ArgumentParser
import re
import csv
from pathlib import Path
import subprocess


def init():
    parser = ArgumentParser()
    parser.add_argument("dirname", nargs='+', help="Give list of folders and/or files for analysis")
    parser.add_argument("-v", help="Output to stdout, no csv-output, unless -o or -w specified", action="store_true")
    parser.add_argument("-w", help="Force writing of csv-file, even if -v option is enabled", action="store_true")
    parser.add_argument("-o", "--outfile", help="Give name of csv-file")
    parser.add_argument("-f", "--force", help="Force analysis of  vertical transition (vt, fc).", action="store_true")
    args = parser.parse_args()
    if args.outfile:
        csvname = Path(args.outfile).expanduser().absolute()
    else:
        csvname = Path.cwd().joinpath('results.csv').expanduser().absolute()
    if csvname.is_file():
        yn = input("%s already exist, overwrite? [y/n] " % csvname)
        if 'y' in yn:
            csvname.unlink()
        else:
            exit(0)

    fls = []
    for dirdir in args.dirname:
        drg = Path(dirdir).expanduser().absolute()
        if drg.is_file():
            fls.append(drg)
        elif drg.is_dir():
            [fls.append(k) for k in drg.glob('./*') if k.is_file()]  # filter out all subdirs
        else:
            print('\"%s\" is no file or dir?' % dirdir)
            continue
    fls.sort()  # in or out the loop? eg do i want to keep user sequence?
    for flname in fls:
        with open(flname, 'r') as fl:
            if 'Welcome to Q-Chem' not in fl.read():  # (faster than re.search)
                continue
        main(flname, outname=csvname, fc=args.force)

    if csvname.is_file():
        with open(csvname, 'r+') as csvfile:
            content = csvfile.read()
            csvfile.seek(0, 0)
            csvfile.write('name, job, time, imag, etot, zpe, esopt, ese, emmE-eV, f, ifweights\n' + content)
        if args.v:
            print()
            with open(csvname, 'r') as csvfile:
                [print(line.rstrip()) for line in csvfile.readlines()]
            if not args.w and not args.outfile:
                csvname.unlink()
    else:
        print('no valid qchem outfiles selected')
        exit(1)


def main(filename, outname, fc=False):
    # def tryapp(applist, dct, key):  # two possibilities: use tryapp, or set defaults, such that no keyerror is given
    #     try:
    #         applist.append(dct[key])
    #     except KeyError:
    #         applist.append('x')
    #     return applist

    basename = filename.name

    splits = splitfile(filename)
    for partfile in splits:
        partfile.esvals(partfile['name'], esnum=1)
        partfile['name'].unlink()
    with open(outname, 'a') as f:
        csvw = csv.writer(f)
        # [print(k) for k in splits]
        print(basename)
        for k in splits:
            row1 = [basename, k['genprops']['job'], k['genprops']['time'], k['genprops']['imag']]
            # if k['gsprops'] is not None:
            #     row1.append(k['gsprops']['gse'])
            #     row1.append(k['gsprops']['zpe'])
            #     if k['esprops'] is None:
            #         row1.append(0)
            row1.append(k['eprops']['etot'])
            row1.append(k['eprops']['zpe'])
            if k['esprops'] != {}:
                es = k['esprops']['es_opt']
                row1.append(es)
                row1.append(k['esprops']['ese'])
                row1.append(k['esprops']['Evt-eV'])
                row1.append(k['esprops']['f'])
                [row1.append(l) for l in k['esprops']['ifcoefs']]
            csvw.writerow(row1)


def splitfile(filein):
    start = False
    dictlist = []
    with open(filein, 'r') as fin:
        for line in fin.readlines():
            if 'Welcome to Q-Chem' in line:
                fileout = filein.parent / (filein.name + '.p%d.pytemp' % len(dictlist))
                dictlist.append(AnaDic())
                dictlist[-1]['name'] = fileout
                start = True
            if start:
                dictlist[-1].analine(line)
                with open(fileout, 'a') as fout:
                    fout.write(line)
    return dictlist


class AnaDic(dict):
    def __init__(self):
        self['name'] = ''
        self['gsprops'] = {}
        self['esprops'] = {}
        self['eprops'] = {'zpe': 0, 'etot': 0}
        self['genprops'] = {'job': None, 'time': 0, 'imag': None, 'err': None}
        super().__init__()

    def analine(self, line):
        jobtype_match = re.search(r"jobtype.*= *([a-z]*)", line, re.IGNORECASE)
        if jobtype_match is not None:
            self['genprops']['job'] = jobtype_match.group(1)
        tote_match = re.search(r"Total energy in the final basis set = +([0-9.-]+)", line)
        imag_match = re.search(r"This Molecule has +([0-9]+) Imaginary Frequencies", line)
        zpe_match = re.search(r"Zero point vibrational energy: +([0-9.-]+) +kcal/mol", line)
        time_match = re.search(r"Total job time: +([0-9.]+)s\(wall\).*", line)
        err_match = re.search('Error termination', line)
        if imag_match is not None:
            self['genprops']['imag'] = int(imag_match.group(1))
        if zpe_match is not None:
            self['eprops']['zpe'] = float(zpe_match.group(1))
        if tote_match is not None:
            self['eprops']['etot'] = float(tote_match.group(1))  # todo include pcm?
        if time_match is not None:
            self['genprops']['time'] += float(time_match.group(1))
        if err_match is not None:
            self['genprops']['err'] = True

    def esvals(self, file, esnum=1):
        script = """
                    sed -nE '/Excited state +%d/,/^$/p' %s | sed -e 's/Excited state/\&\&/' -re 's/[a-Z:)(=>]|\-\-|[a-Z]\.//g' -re 's/ +/ /g' | tr -d '\n'
                    """ % (esnum, file)
        p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        eslist = []
        templist = []
        for num in p.stdout.readline().decode('utf8').split()[1:]:
            try:
                templist.append(float(num))
            except ValueError:
                eslist.append(templist)
                templist = []
        eslist.append(templist)
        if len(eslist[-1]) != 0:
            # esdict = {i: {'emmE-eV': 0, 'emmE-nm': 0, 'f': 0, 's^2': 0, 'ifcoefs': None} for i in range(1, es_max + 1)}
            esdict = {}
            esdict['ese'] = eslist[-1][3]
            esdict['Evt-eV'] = eslist[-1][1]
            esdict['es_opt'] = esnum
            # esdict['s^2'] = eslist[-1][1]
            # tde_match = re.search(r"^ Total Energy, E\(.+\) = +([0-9.-]+)", line)
            # if tde_match is not None:
            #     tde = float(tde_match.group(1))
            # if re.search(r"Triplet", es_match.group(2)):
            #     esdict['f'] = -3
            # else:
            esdict['f'] = eslist[-1][7]
            ifcoefs = []
            for i in range(8, len(eslist[-1])):
                ifcoefs.append(eslist[-1][i])
            esdict['ifcoefs'] = ifcoefs
            self['esprops'] = esdict
        return


def tst():
    main(Path('/home/u0133458/Documents/Calc/un3/qch/antqs0_low.out'), '/home/u0133458/Documents/Calc/un3/qch/rmrm.csv')


if __name__ == '__main__':
    # tst()
    init()
