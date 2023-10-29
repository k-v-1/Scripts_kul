#!/usr/bin/env python3
import sys
import argparse
import re
from pathlib import Path
import numpy as np

def init():
    man = '''get ead from turbomole output files
    first file should be ground state'''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=man)
    parser.add_argument("dirs", type=str, nargs='+', help="add filename[s]")
    parser.add_argument("-d", "--difference", action="store_true", help="output differences in energy wrt gs of molecule")
    parser.add_argument("-c", "--rcm", action="store_true", help="give output in rcm instead of eV")
    args = parser.parse_args()
    dirlst = [Path(i).absolute().expanduser() for i in args.dirs]
    if len(dirlst) == 1:
        elist = gete(dirlst[0])
        print(*elist)
    else:
        elist = []
        for dr in dirlst:
            elist.append(gete(dr))
        gse = elist[0][0]
        if gse > min([i[0] for i in elist]):
            print('gse is not the lowest energy?', file=sys.stderr)
        if args.rcm:
            adia_energs = [[(i-gse)*219475 for i in inner] for inner in elist]
        else:
            adia_energs = [[(i-gse)*27.211386 for i in inner] for inner in elist]
        # [print(*i) for i in adia_energs]
        if not args.difference:
            [print(dirlst[i].stem, *adia_energs[i]) for i in range(len(adia_energs))]

        if args.difference:
            edict = {}
            for i in range(len(adia_energs)):
                edict[dirlst[i].stem] = adia_energs[i]
            diffs = eads(simplify(edict))
            # for mol in diffs:
            #     for diff in diffs[mol]:
            #         print(mol, diff, diffs[mol][diff])
            [print(mol, diff, diffs[mol][diff]) for mol in diffs for diff in diffs[mol]]


def eads(sympdic):
    eaddic = {}
    for mol in sympdic:
        eaddic[mol] = {}
        for stat in sympdic[mol]:
            for stat2 in sympdic[mol]:
                eaddic[mol][str(stat)+str(stat2)] = sympdic[mol][stat]-sympdic[mol][stat2]
    return eaddic


def simplify(edict):
    mols = []
    [mols.append(name[:3]) for name in edict if name[:3] not in mols]
    states = []
    [states.append(name[3:5]) for name in edict if name[3:5] not in states]
    sympdic = {}
    for mol in mols:
        sympdic[mol] = {}
        for stat in states:
            energ = edict[mol+stat+stat[0]][int(stat[1])]
            sympdic[mol][stat] = energ
    return sympdic


def gete(dir):
    gsfile = dir / 'energy'
    esfile = dir / 'exstates'
    gse = 0
    with gsfile.open('r') as gsfl:
        for i, line in enumerate(gsfl.readlines()):
            if i == 1:
                gse = float(line.split()[1])
                break
    ess = []
    with esfile.open('r') as esfl:
        start = -1
        totex = -1
        for line in esfl.readlines():
            if start >= 1 and start <= totex:
                ess.append(float(line.split()[1]))
                start+=1
            if re.search(r'\$excitation_energies_ADC\(2\)', line):
                totex = int(line.split()[-1])
                start = 1
    return [gse] + [i+gse for i in ess]


init()
