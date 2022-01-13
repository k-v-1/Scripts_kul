#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import subprocess


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile1', type=str,
                        help='File to read {abs}data from: gaussian-{log/fchk}')
    parser.add_argument('infile2', nargs='?', type=str, default=None,
                        help='[Optional] File to read {emi,nac}data from: gaussian-{log/fchk}')
    parser.add_argument('infile3', nargs='?', type=str, default=None,
                        help='[Optional] File to read nac-data from: gaussian-{log/fchk}')
    parser.add_argument('-e', '--eldip', nargs='?', type=str, default=None, const='edm.fcc',
                        help='extract eldips in edm.fcc or [name]')
    parser.add_argument('-m', '--magdip', nargs='?', type=str, default=None, const='mdm.fcc',
                        help='extract magdips in mdm.fcc or [name]')
    parser.add_argument('-n', '--nacme', nargs='?', type=str, default=None, const='nac.fcc',
                        help='extract nacme in nac.fcc or [name]')
    parser.add_argument('-s', '--states', nargs='+', type=int, default=[1],
                        help='Electronic state(s), when only one state: assuming 0-->n (default n=1)')
    parser.add_argument("-o", "--mmpnac", action="store_true", help="Use old nacme-approximation (used in momap)")
    parser.add_argument("-r", "--root", action="store_true", help="Extract root from file")
    args = parser.parse_args()
    cwd = Path.cwd()

    file1 = Path(args.infile1).expanduser().absolute()
    file2 = Path(args.infile2).expanduser().absolute() if args.infile2 is not None else None
    file3 = Path(args.infile3).expanduser().absolute() if args.infile3 is not None else None
    # Check existence of files
    for infile in file1, file2, file3:
        if infile is not None and not infile.is_file():
            print(f'{infile} is not a file', file=sys.stderr)
            exit(1)

    # Parse excited state numbers; if given one: transition from 0 to n. (only one implemented)
    if len(args.states) == 1:
        stnum = args.states[0]  # [-1] == [0]
    elif len(args.states) == 2:
        if args.states[0] == 0:
            stnum = args.states[1]
        else:
            print(f'state {args.states[0]} to state {args.states[1]} not yet implemented', file=sys.stderr)
            exit(2)
    else:
        print('number of states should be 1 or 2', file=sys.stderr)
        exit(1)
    if args.root:
        filer = [i for i in [file1, file2] if i is not None][-1]
        stnum = eval(filer.suffix[1:]+f'_get_root("{filer}")')

    if args.eldip is not None:
        edmfile = cwd / args.eldip
        edmfile.touch()
        if edmfile.stat().st_size > 2000:
            print("nac-file already exist and is large, first delete this file manually", file=sys.stderr)
            exit(2)
        suf1 = file1.suffix[1:]
        # noinspection PyUnboundLocalVariable
        ellst = eval(suf1 + f'_em("{file1}",{stnum},"e")')
        if ellst:
            with open(edmfile, "w") as wr:
                wr.write(" ".join(ellst) + '\n')
        else:
            print(f"no eldips in file {file1}", file=sys.stderr)
        if file2 is not None:
            suf2 = file2.suffix[1:]
            ellst2 = eval(suf2 + f'_em("{file2}",{stnum},"e")')
            if ellst2:
                with open(edmfile, "a") as wr:
                    wr.write(" ".join(ellst2) + '\n\n')
            else:
                print(f"no eldips in file {file2}", file=sys.stderr)

    if args.nacme is not None:
        inflst = [i for i in [file1, file2, file3] if i is not None]
        filen = inflst[-1]
        sufn = filen.suffix[1:]
        if args.mmpnac:
            naclst = eval(sufn + f'_mmpnac("{filen}",{args.states[-1]})')
        else:
            naclst = eval(sufn + f'_nac("{filen}",{args.states[-1]})')
        nacfile = cwd / args.nacme
        nacfile.touch()
        if sum(naclst) == 0:
            print("nacme's are all zero")
        elif nacfile.stat().st_size < 2000:
            with open(nacfile, "w") as wr:
                for i in range(0, len(naclst), 3):
                    wr.write(" ".join([str(i) for i in naclst[i:i + 3]]) + '\n')
                wr.write("\n")
        else:
            print("nac-file already exist and is large, first delete this file manually", file=sys.stderr)

    if args.magdip is not None:
        print('magdip not yet implemented', file=sys.stderr)
        exit(2)


# The information is in "ETran ..." sections:
#  *"ETran scalars" contains:
#    <number of ES> <?> <?> <?> <target state> <?>
#     0 0 0...
#  *"ETran state values"  contains
#    ·First the properties of each excited state (up to Nes):
#    1,  2   , 3  , 4  , 5     , 6     , 7     , 8    , 9    , 10   ,        11,12,13,14 15,16 ...
#    {E, muNx,muNy,muNz,muvelNx,muvelNy,muvelNz,mmagNx,mmagNy,mmagNz,quadrvelXX,YY,ZZ,XY,XZ,YZ}_N=1,Nes
# # # This is wrong in the gaussian_manage.f90 file
#    ·Then, the derivates of each property with respect to Cartesian coordiates only for target state
#     For each Cartesian coordiate, all derivatives are shown:
#     dE/dx1 dmux/dx1 dmuy/dx1 ... quadrvelYZ/dx1
#     dE/dy1 dmux/dy1 dmuy/dy1 ... unkZ/dy1
#     ...
#     dE/dzN dmux/dzN dmuy/dzN ... unkZ/dzN
def fchk_get_root(fcfl):
    script = f"sed '/Route/,/Charge/!d' {fcfl} | tr '\n' ' ' |sed -e 's/ //g; s/^.*[rR][oO][oO][tT][=]\([0-9]\).*/\\1/'"
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    return int(p.stdout.readline().decode('utf8'))


def fchk_em(fcfl, esn, em):
    nlines = esn * 16 // 5 + 1
    if em == 'e':
        n1 = esn * 16 - 15  # Python starts at 0
    elif em == 'm':
        n1 = esn * 16 - 9
    else:
        print('em should be "e"lectronic or "m"agnetic', file=sys.stderr)
        exit(1)
    script = f"grep -F -A{nlines} 'ETran state values' {fcfl} | tail -n+2 | tr '\n' ' '"
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    etran = p.stdout.readline().decode('utf8').split()
    return etran[n1:n1 + 3]


def log_em(fcfl, esn, em):
    emdic = {'e': 'electric', 'm': 'magnetic'}
    script = f"grep -F -A{esn + 1} 'transition {emdic[em]} dipole moments' {fcfl} | tail -n1 | awk '{{print $2, $3, $4}}'"
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    etran = p.stdout.readline().decode('utf8').split()
    return etran


def fchk_nac(fcfl, esn=1):
    # todo: to think: is checking esn necessary?

    # first try faster? method, then grepping 2 times on same file
    script = """
    filename=%s
    atnum=($(head $filename  | grep -F 'Number of atoms' | awk '{print $5}'))
    if [[ "x$atnum" != "x" ]]; then 
    grep -F -A$((${atnum}*3/5+1)) 'Nonadiabatic coupling' $filename | tail -n+2 | tr '\n' ' '
    else
    nat3=($(grep "Nonadiabatic coupling" $filename | awk '{print $5}'))
    grep -F -A$((${nat3}/5+1)) 'Nonadiabatic coupling' $filename | tail -n+2 | tr '\n' ' '
    fi
    """ % fcfl
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    naclst = [float(f) for f in p.stdout.readline().decode('utf8').split()]
    return naclst


def log_nac(fcfl, esn=1):
    script = """
    filename=%s
    atnum=($(grep -F 'NAtoms=' $filename  | awk '{print $2}'))
    grep -F -A$((${atnum}+2)) 'Nonadiabatic Coup' $filename | tail -n${atnum} | awk '{print $3, $4, $5}' | tr '\n' ' '
    """ % fcfl
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    naclst = [float(f) for f in p.stdout.readline().decode('utf8').split()]
    return naclst


def log_mmpnac(fcfl, esn=1):
    script = """
    filename=%s
    atnum=($(grep -F 'NAtoms=' $filename  | awk '{print $2}'))
    grep -F -A$((${atnum}+2)) 'Coordinates (Angstroms)' $filename | tail -n${atnum} | awk '{print $2}' | tr '\n' ' '
    echo
    grep -F -A$((${atnum}+2)) 'Electric Field' $filename | tail -n${atnum} | awk '{print $3, $4, $5}' | tr '\n' ' '
    """ % fcfl
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    start = True
    naclst, zlst = [], []
    for line in p.stdout.readlines():
        if start:
            zlst = [int(f) for f in line.decode('utf8').split()]
            start = False
        else:
            naclst = [float(tef) * zlst[fn // 3] for fn, tef in enumerate(line.decode('utf8').split())]
    return naclst


if __name__ == '__main__':
    init()
