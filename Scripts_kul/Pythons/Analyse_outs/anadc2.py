#!python3
import csv
import re
from argparse import ArgumentParser
from pathlib import Path

#todo: ess on different lines if ifcoefs is printed, but make option to do oneliner without ifcoefs (default)

def init():
    parser = ArgumentParser()
    parser.add_argument("dirname", nargs='+', help="Give list of folders and/or files for analysis")
    parser.add_argument("-v", "--verbose", help="Output to stdout, no csv-output, unless -o or -w specified",
                        action="store_true")
    parser.add_argument("-w", help="Force writing of csv-file, even if -v option is enabled", action="store_true")
    parser.add_argument("-o", "--outfile", help="Give name of csv-file")
    parser.add_argument("-l", "--long", help="Long multiline output.", action="store_true")
    parser.add_argument("-s", "--space", help="More readable output by adding Space between words. Same as -r",
                        action="store_true")
    parser.add_argument("-r", "--readable", help="More readable output by adding Space between words. Same as -s",
                        action="store_true")
    parser.add_argument("-t", "--time", help="Output time in seconds instead of hours.", action="store_true")
    parser.add_argument("-e", "--effi", help="Output efficiency instead of time (t_cpu/t_elapsed).", action="store_true")
    args = parser.parse_args()
    if args.effi:
        args.time = True
    if args.outfile:
        csvname = Path(args.outfile).expanduser().absolute()
    else:
        csvname = Path.cwd().joinpath('results.csv').expanduser().absolute()
    if csvname.is_file():
        yn = input("file already exist, overwrite? [y/n] ")
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
        try:
            with open(flname, 'r') as fl:
                # if 'TURBOMOLE V7.1' not in fl.read():  # (faster than re.search)
                if not re.search(r'ricc2 .* TURBOMOLE V7\.1',fl.read(),re.MULTILINE):
                    continue
            main(flname, outname=csvname, long=args.long, t_unit=args.time, eff=args.effi)
        except UnicodeError:
            continue

    if csvname.is_file():
        with open(csvname, 'r+') as csvfile:
            content = csvfile.read()
            csvfile.seek(0, 0)
        if args.verbose:
            print()
            with open(csvname, 'r+') as csvfile:
                if args.space or args.readable:
                    pass
                    # csvfile.write('name, o/f, time, imag, gse/ese, zpe, esopt, emmE-eV, f, ifweights\n' + content)
                    # colms = [ln.split(',')[0:3] for ln in csvfile.readlines()]
                    # csvfile.seek(0, 0)
                    # namelen = max([len(st[0]) for st in colms])
                    # timelen = max([len(st[2]) for st in colms])
                    # for line in csvfile.readlines():
                    #     ll = line.replace('\n', '').replace('ifweights', 'i,f,999').split(',')
                    #     [ll.append('') for _ in range(9 - len(ll))]

                    #     def fun(x, y): return x + ' ' * (y - len(x))

                    #     ifcoefs = [', '.join(ll[i + 9:i + 12]) for i in range(0, len(ll[9:]), 3) if
                    #                float(ll[i + 11]) > 0.2]
                        # print(f"{fun(ll[0], namelen)}, {fun(ll[1], 13)}, {fun(ll[2], timelen)}, {fun(ll[3], 5)},"
                            #   f"{fun(ll[4], 14)}, {fun(ll[5], 8)}, {fun(ll[6], 6)}, {fun(ll[7], 7)}, {fun(ll[8], 6)}, "
                            #   f"{', '.join(ifcoefs)}")
                else:
                    csvfile.write('name, err, time, es, s^2, emmE-eV, f, es, s^2, emmE-eV, f, es, s^2, emmE-eV, f\n'+ content)
                    [print(line.rstrip()) for line in csvfile.readlines()]
            if not args.w and not args.outfile:
                csvname.unlink()
    else:
        print('no valid turb-adc(2) logfiles selected')
        exit(1)


def main(infile, outname, long=False, t_unit=False, eff=False):
    with open(outname, 'a') as f:
        name = infile.parent.name
        csvw = csv.writer(f)
        print(name)  # , filedict)
        filedict = start_ana(infile, t_unit)
        if eff:
            filedict['wall'] = round(filedict['cpu']/filedict['wall']/filedict['nds']*100,2)
        if long:
            pass
            # [row1.append(k) for k in filedict['esprops']['esdict'][es]['ifcoefs']]
        else:
            row1 = [name, filedict['err'], filedict['wall'], filedict['mp2_E']]
            for es in filedict['esprops']:
                row1.append(es)
                esd = filedict['esprops'][es]
                row1.append(esd['s2'])
                row1.append(esd['emmE-eV'])
                row1.append(esd['f'])
            csvw.writerow(row1)


def dhms2time(d, h, m, s, unit=False):
    if unit:
        return float(d) * 86400 + float(h) * 3600 + float(m) * 60 + float(s)
    else:
        return float(d) * 24 + float(h) + float(m) / 60 + float(s)/3600


def start_ana(totfile, t_unit=False):
    filedic = {'mp2_E': 0, 'nds':0, 'cpu':0, 'wall': 0, 'err': True, 'esprops': None}
    esdict = {i: {'emmE-eV': 0, 'f': 0, 's2': 0, 'ifcoefs': []} for i in range(1, 4)}

    with open(totfile, "r") as fl:
        cosmo, ifstart = False, False
        esnum, esnumc = 0, 0
        for line in fl.readlines():
            # nodes
            nds_match = re.search(r'program will use ([0-9]+) ', line)
            if nds_match is not None:
                filedic['nds'] = int(nds_match.group(1))
            if not cosmo and re.search('COSMO switched on', line):
                cosmo = True
            if cosmo:
                continue
            else:
                ##gas
                #gs-energy
                if filedic['mp2_E'] == 0:
                    mp2_match = re.search(r'^ {5}\*   Final MP2 energy {24}\: +([0-9.-]+) +\*', line)
                if mp2_match is not None:
                    filedic['mp2_E'] = float(mp2_match.group(1))

                #energies, multis and osc strength
                esmatch = re.search(r'^  \| +number, symmetry, multiplicity: +([0-9]+) a    ([0-9])', line)
                if esmatch is not None:
                    esnum = int(esmatch.group(1))
                    esdict[esnum]['s2']=int(esmatch.group(2))
                if esnum != 0:
                    freqmatch = re.search(r'^  \| +frequency : +[0-9.-]+ a\.u\. +([0-9.-]+) e\.V\.', line)
                    if freqmatch is not None:
                        esdict[esnum]['emmE-eV']=float(freqmatch.group(1))
                    f_match = re.search(r'oscillator strength \(length gauge\) +: +([0-9.-]+)', line)
                    if f_match is not None:
                        esdict[esnum]['f'] = float(f_match.group(1))
                        esnum = 0

            #ifcoefs: both gas and cosmo
            ifsmatch = re.search(r'type: RE0 +symmetry: a +state: +([0-9]+)', line)
            if ifsmatch is not None:
                ifstart = True
                esnumc = int(ifsmatch.group(1))
            if ifstart:
                ifmatch = re.search(r' +\| ([0-9]+) a +[0-9]+ +\| +([0-9]+) a +[0-9]+ +\|[0-9.-]+ +([0-9.]+) +\|', line)
                if ifmatch is not None:
                    # print(esdict[esnumc]['ifcoefs'])#.append(ifmatch.group(1))
                    [esdict[esnumc]['ifcoefs'].append(ifmatch.group(i)) for i in [1,2,3]]
                if re.search('norm of printed elements', line):
                    ifstart = False

            #time
            if re.search(r'total .*-time :', line):
                tnums = [i for i in line.split() if i.isdecimal()]
                tnums = [0]*(4-len(tnums)) + tnums
                t_name = line.split()[1].split('-')[0]
                filedic[t_name] = dhms2time(*tnums, unit=t_unit)
            if re.search('ricc2 : all done', line):
                filedic['err'] = False
    filedic['esprops'] = esdict

    return filedic


if __name__ == '__main__':
    init()
