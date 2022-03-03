#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
# import matplotlib.pyplot as plt
import numpy as np
import math
import subprocess
import littlescripts as lts
import sys

# uconv = {'nm': 1239.849, 'rcm': 8065.5, 'cm-1': 8065.5, 'ev': 1}
# colconv = {'nm': 3, 'rcm': 2, 'cm-1': 2, 'ev': 1}
fntsz = 10
lnsz = 0.8


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', type=str, nargs='+',
                        help='Folders containing output files [and rate_vs_ead-file]')
    # parser.add_argument('-i', '--info', action='store_true', help='Show only in&output information')
    # parser.add_argument('-u', '--unit', type=str.lower, help='eV, nm, rcm=cm-1', default='ev')
    # parser.add_argument('-a', '--axis', type=float, nargs=2, help='specify x-axis values', default=None)
    args = parser.parse_args()

    # TODO: Check all files on content and determine like this what filename to use for data obtaining

    header = True
    for dirstr in args.folders:
        drg = Path(dirstr).expanduser().absolute()
        if not drg.is_dir():
            continue  # TODO: More checks!
        print(dirstr)
        outlst = getfl(drg)
        if header:
            print('name, Ead (eV), l/g, FWHM (rcm), rate (s-1), rate_spec')
            header = False
        for outfl, outprop in outlst:
            # print(outfl.parent.relative_to(Path.cwd()))
            datdic, rate = inf_main(outfl, outprop)
            prntln = f"{outfl.parent.relative_to(Path.cwd())}, {(datdic['Ead'] * 27.212):.3f}, "\
                     f"{datdic['BroadenType'][0:3]}, {(datdic['FWHM'] * 219474):.2e}, " \
                     f"{rate:.3e}, {datdic['rtsfsp']:.3e}"
            print(prntln)


def getfl(folder, ext=''):
    foutlst = []
    fldr_lst = list(Path(folder).expanduser().absolute().glob(f'./**/*{ext}'))
    for isfl in [f for f in fldr_lst if f.is_file()]:
        with open(isfl, 'rb',buffering=0) as fl:
            a = str(fl.read(2000))
            if re.search('FCCLASSES3', a):
                prop = re.search(r'PROPERTY += +([A-Z0-9]+)', a)
                if prop is not None:
                    foutlst.append((isfl, prop.group(1)))
                else:
                    print(f'Error, property not found: {isfl}', file=sys.stderr)
    return foutlst


def getinp(filepath):  # FWHM in a.u.
    script = ''
    infdic = {'Temp': -math.inf, 'Ead': -math.inf, 'tmax:': -math.inf, 'dt': -math.inf, 'points': -math.inf,
                'isgauss': '-', 'BroadenType': '-', 'FWHM': -math.inf, 'Broadenfunc': '-'}
    script = """
                cat <<'END' | sh | xargs echo
                fl=%s
                grep -F "Temperature" $fl | awk '{print "Temp",$3}'
                grep -F -A1 "ADIABATIC ENERGY" $fl | tail -n1 | awk '{print "Ead", 0.0367484*$1}'
                # grep "Total time" $fl | awk '{print "tmax",41.341373*$4}'
                # grep "Time step" $fl | awk '{print "dt",41.341373*$5}'
                # grep "data points" $fl | awk '{print "points",$5}'
                grep -F "tfin  =" $fl | awk '{print "tmax",41.341373*$3}'
                grep -F "dt    =" $fl | awk '{print "dt",41.341373*$3}'
                grep -F "ntime =" $fl | awk '{print "points",$3}'
                grep -F "Broad. function" $fl | awk '{print "BroadenType",$4}'
                grep -E "HWHM {9}=" $fl | awk '{print "FWHM",2*0.0367485*$3}'
                grep -F "Broad. exponent" $fl | awk '{print "brexp", $4}'
END
                """ % filepath  # Total time, timestep etc not working with TI --> tfin, dt, ntime
        # TODO BROADFUN search for TI-case?
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    inflist = p.stdout.readline().decode('utf8').split()
    for i in range(len(inflist) // 2):
        try:
            infdic[inflist[2 * i]] = float(inflist[2 * i + 1])
        except ValueError:
            infdic[inflist[2 * i]] = inflist[2 * i + 1]
    return infdic


def rates(filepath, prop):
    search_dic = {'EMI': 'kr(s-1) =',
                  'IC': 'IC rate constant (s-1)',
                  'NR0': 'rate constant (s-1)'}
    if prop not in search_dic:
        return 0
    # watch out for r-string (no escape needed) and -E flag
    script = fr"tail -n100 {filepath} | grep '{search_dic[prop]}' | sed -E 's/^.* ([-]?[0-9]+[.]?[0-9]*E?[0-9-]*)/\1/'"
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash').stdout
    try:
        return float(p.readline().decode('utf8'))
    except ValueError:
        return None


def times(filepath):
    script = "tail %s | grep 'CPU (s)   ' | awk '{print $3}'" % filepath
    # Speeding up with tail! # no use of f-string, due to {}'s
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash').stdout
    return float(p.readline().decode('utf8'))


def rts_from_spec(filepath, ead, points=10):  # todo: how to choose points?; #todo: Show graph?; .......
    plotfile = [y for y in filepath.parent.glob('k??_vs_Ead_T?.dat')][0]
    fomat = np.genfromtxt(plotfile)
    fo_smo = lts.smooth(fomat[:, 1], points)
    # fo_smo = fomat[:, 1]
    xval = lts.closest(fomat[:, 0], ead)
    yval = fo_smo[list(fomat[:, 0]).index(xval)]
    try:
        ytestval = fo_smo[list(fomat[:, 0]).index(xval) + 1]
    except IndexError:
        print(
            f'{filepath.parts[-1]}      ,kic-val on edge of plotted region? index =, {list(fomat[:, 0]).index(xval)}, {len(fo_smo)}')
        ytestval = fo_smo[list(fomat[:, 0]).index(xval) - 1]
    smoothmessage = f'{filepath.parts[-1]}      , SmoothingNotComplete!, {yval:0.2e}, {ytestval:0.2e}'
    try:
        if math.log10(ytestval) - math.log10(yval) > 0.05:
            print(smoothmessage)
    except ValueError:
        print(smoothmessage)

    return yval


def inf_main(flname, prop):
    datdic = getinp(flname)
    if prop in ['EMI', 'IC', 'NR0']:
        rt = rates(flname, prop)
        if rt is None:
            rt = 0
            print(f'Error: No rates in file? {flname.relative_to(Path.cwd())}')
    else:
        rt = 0
    if prop in ['IC', 'NR0']:
        datdic['rtsfsp'] = rts_from_spec(flname, datdic['Ead'] * 27.212)
    else:
        datdic['rtsfsp'] = 0

    if datdic['isgauss'] == '.f.':
        datdic['BroadenType'], datdic['FWHM'], datdic['Broadenfunc'] = '-', '-', '-'
    if re.search('LOR', datdic['BroadenType']):  # more exact fwhm
        datdic['FWHM'] = datdic['brexp'] * 2
    elif re.search('GAU', datdic['BroadenType']):
        datdic['FWHM'] = 2 * math.sqrt(
            2 * datdic['brexp'] / (math.sqrt(2 * math.log10(2))))  # todo: test this expression
    return datdic, rt
    # return datdic['Ead'] * 27.212,datdic['BroadenType'],  datdic['FWHM'] * 219474, rt, datdic['rtsfsp']

    # prntln = f"{flname.parts[-1]}, {(datdic['Ead'] * 27.212):.3f}, {datdic['BroadenType'][0:3]}, {(datdic['FWHM'] * 219474):.2e}, " \
    #          f"{rt:.3e}, {datdic['rtsfsp']:.3e}"
    # if str(datdic['rtsfsp'])[0:2] == str(rt)[0:2]:
    #     prntln = prntln.rsplit(' ', 1)[0]


if __name__ == '__main__':
    init()
