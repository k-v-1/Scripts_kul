#!/usr/bin/env python3
import csv
from math import floor, log10
import re
from argparse import ArgumentParser
from pathlib import Path

# structure:
"""
init --> checks files, inits csv-file
     --> calls main
     --> prints csv-file
    main --> calls start_ana
         --> writes to csv-file
        start_ana --> analyses outputfile
                    = nodes, energy, time, error, multiplicity, osc. strength, orbital coefs, ...
"""
#very meta-stable, only works on specific single point adc(2) calculations

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
    parser.add_argument("-E", "--Etot", help="Output total energies of states.", action="store_true")
    parser.add_argument("-T", "--TDM", help="Output total energies of states.", action="store_true")
    args = parser.parse_args()
    if args.effi:
        args.time = True
    addspace = args.space or args.readable
    if args.outfile:
        csvname = Path(args.outfile).expanduser().absolute()
    else:
        csvname = Path.cwd().joinpath('results.csv').expanduser().absolute()

    def file_parser_2_main():
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
                    # if not 'TURBOMOLE V7.1' not in fl.read():  # (faster than re.search)
                    if not re.search(r'ricc2 .* TURBOMOLE V7\.1', fl.read(2000), re.MULTILINE):
                        continue
                main(flname, outname=csvname, long=args.long, t_unit=args.time, eff=args.effi, roundnum=addspace, tote=args.Etot, tdm=args.TDM)
            except UnicodeError:
                continue

    if not csvname.is_file():
        file_parser_2_main()
    else:
        yn = input("file already exist, overwrite? [y/n] ")
        if 'y' in yn:
            csvname.unlink()
            file_parser_2_main()
        else:
            yn = input("Continue? [y/n] ")
            if 'n' in yn:
                exit(0)

    if csvname.is_file():
        with open(csvname, 'r+') as csvfile:
            content = csvfile.read()
            csvfile.seek(0, 0)
            csvfile.write('name,err,time,mp2,es,s^2,emE-eV,f,es,s^2,emE-eV,f,es,s^2,emE-eV,f\n'+ content)
        if args.verbose:
            def fun(x, y): return ' ' * (y - len(x)) + x
            print()
            with open(csvname, 'r') as csvfile:
                if addspace:
                    if args.long:
                        colms = [ln.split(',')[0:3] for ln in csvfile.readlines()]
                        namelen = max([len(st[0]) for st in colms])
                        timelen = max([len(st[2]) for st in colms])
                        esprint, gsprint = [], []
                        csvfile.seek(0, 0)
                        for line in csvfile.readlines():
                            ll = line.replace('\n', '').replace('False', '').replace('ifweights', 'i,f,999').split(',')
                            if len(ll) == 4:
                                gsprint.append(f"{fun(ll[0], namelen+1)},{fun(ll[1], 4)},{fun(ll[2], timelen+1)},{fun(ll[3], 12)}\n")
                            elif len(ll) == 16 and ll[0] == 'name':
                                gsprint.append(f" {fun(ll[0], namelen+1)},{fun(ll[1], 4)},{fun(ll[2], timelen+1)},{fun(ll[3], 12)}\n")
                                esprint.append('es,s2,  emE-eV,          f,  i,  f, %\n')
                            else:
                                ifcoefs = [', '.join(ll[i + 4:i + 7]) for i in range(0, len(ll[4:]), 3) if float(ll[i + 6]) > 5]
                                esprint.append(f"{fun(ll[0], 2)},{fun(ll[1], 2)},{fun(ll[2], 8)},{fun(ll[3], 11)}, {', '.join(ifcoefs)}\n")
                        print(*gsprint, '\n', *esprint)
                    else:
                        colms = [ln.split(',')[0:3] for ln in csvfile.readlines()]
                        csvfile.seek(0, 0)
                        namelen = max([len(st[0]) for st in colms])
                        timelen = max([len(st[2]) for st in colms])
                        for line in csvfile.readlines():
                            ll = line.replace('\n', '').replace('False', '').replace('ifweights', 'i,f,999').split(',')
                            # [ll.append('') for _ in range(9 - len(ll))]
                            print(f"{fun(ll[0], namelen+1)},{fun(ll[1], 4)},{fun(ll[2], timelen+1)},{fun(ll[3], 12)} ,|"
                                f"{fun(ll[4], 3)},{fun(ll[5], 4)},{fun(ll[6], 7)},{fun(ll[7], 6)} ,|"
                                f"{fun(ll[8], 3)},{fun(ll[9], 4)},{fun(ll[10], 7)},{fun(ll[11], 6)} ,|"
                                f"{fun(ll[12], 3)},{fun(ll[13], 4)},{fun(ll[14], 7)},{fun(ll[15], 6)}")
                else:
                    [print(line.rstrip().replace(',6,0,0,0','').replace(',5,0,0,0','').replace(',4,0,0,0','')) for line in csvfile.readlines()]
            if not args.w and not args.outfile:
                csvname.unlink()
    else:
        print('no valid turb-adc(2) logfiles selected')
        exit(1)


def main(infile, outname, long=False, t_unit=False, eff=False, roundnum=False, tote=False, tdm=False):
    with open(outname, 'a') as f:
        name = infile.parent.relative_to(Path.cwd())
        # name = infile.parent.parent.name
        csvw = csv.writer(f)
        print(name)  # , filedict)
        filedict = start_ana(infile, t_unit)
        # print(filedict)
        if eff:
            filedict['wall'] = round(filedict['cpu']/filedict['wall']/filedict['nds']*100,2)
        else:
            filedict['wall'] = round(filedict['wall'], 2-int(floor(log10(abs(filedict['wall'])+0.00001))))
        if tote:
            csvw.writerow([name, filedict['mp2_E']])
            [csvw.writerow([es, filedict['esprops'][es]['emmE-au']+filedict['mp2_E']]) for es in filedict['esprops']]
            # csvw.writerow([name, *[es for es in filedict['esprops']]])
            # csvw.writerow([filedict['mp2_E'], *[filedict['esprops'][es]['emmE-au']+filedict['mp2_E'] for es in filedict['esprops']]])
        if tdm:
            row1 = []
            for es in filedict['esprops']:
                esd = filedict['esprops'][es]
                csvw.writerow([es, *[f'{ls[0]}{ls[1]}' for ls in esd['tdm']]])
                csvw.writerow([es, *[ls[2] for ls in esd['tdm']]])
        if long:
            csvw.writerow([name, filedict['err'], filedict['wall'], filedict['mp2_E']])
            for es in filedict['esprops']:
                esd = filedict['esprops'][es]
                row1 = [es, esd['s2'], esd['emmE-eV'], esd['f']]
                [row1.append(k) for k in esd['ifcoefs']]
                csvw.writerow(row1)
        elif roundnum:
            filedict['mp2_E'] = round(filedict['mp2_E'], 6)
            row1 = [name, filedict['err'], filedict['wall'], filedict['mp2_E']]
            for es in filedict['esprops']:
                row1.append(es)
                esd = filedict['esprops'][es]
                esd['emmE-eV'] = round(esd['emmE-eV'], 4)
                esd['f'] = round(esd['f'], 3)
                row1.append(esd['s2'])
                row1.append(esd['emmE-eV'])
                row1.append(esd['f'])
            csvw.writerow(row1)

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
    filedic = {'mp2_E': 0, 'nds':0, 'cpu':-1, 'wall': -1, 'err': True, 'esprops': None}
    esdict = {i: {'emmE-eV': 0, 'f': 0, 's2': 0, 'ifcoefs': [], 'tdm': []} for i in range(1, 7)}

    with open(totfile, "r") as fl:
        cosmo, ifstart, tdm_start = False, False, False
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
                elif esnum != 0:
                    freqmatch = re.search(r'^  \| +frequency : +([0-9.-]+) a\.u\. +([0-9.-]+) e\.V\.', line)
                    f_match = re.search(r'oscillator strength \(length gauge\) +: +([0-9.-]+)', line)
                    dip_match = re.search(r'([xyz])diplen +[|] +[0-9.-]+[ |]+[0-9.-]+[ |]+([0-9.-]+)', line)
                    if freqmatch is not None:
                        esdict[esnum]['emmE-au'] = float(freqmatch.group(1))
                        esdict[esnum]['emmE-eV'] = float(freqmatch.group(2))
                    elif dip_match is not None:
                        esdict[esnum]['tdm'].append([0, str(dip_match.group(1)), float(dip_match.group(2))])
                    elif f_match is not None:
                        esdict[esnum]['f'] = float(f_match.group(1))
                        esnum = 0
                #es-es-tdms
                pair_match = re.search(r'Transition moments for pair +([0-9]+) .+ ([0-9]+) ', line)
                if pair_match is not None:
                    eses1 = int(pair_match.group(1))
                    eses2 = int(pair_match.group(2))
                    tdm_start = True
                if tdm_start:
                    dip2_match = re.search(r'([xyz])diplen +[0-9.-]+ +[0-9.-]+ +([0-9.-]+)', line)
                    if dip2_match is not None:
                        esdict[eses1]['tdm'].append([eses2, str(dip2_match.group(1)), dip2_match.group(2)])
                        # esdict[eses1]['tdm'].append(eses2)
                        # esdict[eses1]['tdm'].append(str(dip2_match.group(1)))
                        # esdict[eses1]['tdm'].append(dip2_match.group(2))
                        if str(dip2_match.group(1)) == 'z':
                            tdm_start=False

            #ifcoefs: both gas and cosmo
            ifsmatch = re.search(r'type: RE0 +symmetry: a +state: +([0-9]+)', line)
            if ifsmatch is not None:
                ifstart = True
                esnumc = int(ifsmatch.group(1))
            if ifstart:
                ifmatch = re.search(r' +\| +([0-9]+) a +[0-9]+ +\| +([0-9]+) a +[0-9]+ +\| +[0-9.-]+ +([0-9.]+) +\|', line)
                if ifmatch is not None:
                    # print(ifmatch)
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
