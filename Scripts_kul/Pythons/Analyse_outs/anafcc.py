#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import matplotlib.pyplot as plt
import numpy as np
import math
import subprocess
import littlescripts as lts
import sys

############
# init: args from terminal: dirs of outputfiles
#   --> get_fl
#   --> inf_main
# get_fl: folder -> list of valid output files
# inf_main: file -> datdic + rate
#   --> getinp
#   --> rates
#   --> rts_from_spec
#   getinp: file -> infdic = temp, ead, t's, broad's,..
#   rates:  file -> rate
#   rts_from_spec: file -> rate (via k??_vs_ead.dat in same folder)
############

uconv = {'nm': 1239.849, 'rcm': 8065.5, 'cm-1': 8065.5, 'ev': 1}
# colconv = {'nm': 3, 'rcm': 2, 'cm-1': 2, 'ev': 1}
fntsz = 10
lnsz = 0.8


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', type=str, nargs='+',
                        help='Folders containing output files [and rate_vs_ead-file]')
    parser.add_argument('-e', '--ext', default='',type=str, help='extension for outputfiles (.out, .log, , ...)')
    parser.add_argument('-s', '--spec', action='store_true', help='Show spectra for abs, emi', default=False)
    parser.add_argument('-o', '--onefig', action='store_true', help='spec: add all graphs from a dir in 1 fig', default=False)
    parser.add_argument('-u', '--unit', type=str.lower, help='spec: choose eV, nm, rcm=cm-1', default='ev')
    parser.add_argument('-a', '--axis', type=float, nargs=2, help='spec: choose x-axis limits', default=None)

    parser.add_argument('-K', '--Kicspec', action='store_true', help='Show spectra for IC, NR0', default=False)
    parser.add_argument('-O', '--Onefig', action='store_true', help='KicSpec: add all graphs from a dir in 1 fig', default=False)
    parser.add_argument('-U', '--Unit', type=str.lower, help='KicSpec: choose eV, nm, rcm=cm-1', default='ev')
    parser.add_argument('-P', '--Points', type=int, help='KicSpec: number of points for smoothing', default=10)
    args = parser.parse_args()

    # TODO: Check all files on content and determine like this what filename to use for data obtaining

    header = True
    if args.onefig:
        args.spec = True
    if args.Onefig:
        args.Kicspec = True
    do_kicspec = {'spec':args.Kicspec, 'unit':args.Unit, 'onefig':args.Onefig, 'points':args.Points}
    do_spec = {'spec':args.spec, 'unit':args.unit, 'onefig':args.onefig, 'axis': args.axis}
    def ratestr(rate):
        try:
            return f"{rate:.3e}"
        except ValueError:
            return rate

    for dirstr in args.folders:
        drg = Path(dirstr).expanduser().absolute()
        if not drg.is_dir():
            continue  # TODO: More checks!
        print(dirstr)
        outlst = getfl(drg, ext=args.ext)
        if header:
            print('name, Ead (eV), l/g, FWHM (rcm), rate (s-1), rate_spec')
            header = False
        for outfl, outprop in outlst:
            # print(outfl.parent.relative_to(Path.cwd()))
            datdic, rate = inf_main(outfl, outprop, do_spec, do_kicspec)
            prntln = f"{outfl.parent.relative_to(Path.cwd())}, {(datdic['Ead'] * 27.212):.3f}, "\
                     f"{datdic['BroadenType'][0:3]}, {(datdic['FWHM'] * 219474):.2e}, " \
                     f"{ratestr(rate)}, {ratestr(datdic['rtsfsp'])}"
            print(prntln)
            # if plt.gca().get_legend_handles_labels() !=([],[]):
            if args.Kicspec or args.spec:
                plt.legend()
    if args.Kicspec or args.spec:
        plt.show()


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


def rts_from_spec(datfile, ead, points=10, spec=True, unit='ev', onefig=False):  # todo: how to choose points?; #todo: Show graph?; .......
    # plotfile = [y for y in filepath.parent.glob('k??_vs_Ead_T?.dat')][0]
    label = str(datfile.parent.relative_to(Path.cwd()))
    fomat = np.genfromtxt(datfile)
    y_smo = lts.smooth(fomat[:, 1], points)
    # fo_smo = fomat[:, 1]
    xval = lts.closest(fomat[:, 0], ead)
    yval = y_smo[list(fomat[:, 0]).index(xval)]
    try:
        ytestval = y_smo[list(fomat[:, 0]).index(xval) + 1]
    except IndexError:
        print(f'{label}      ,kic-val on edge of plotted region? index =, {list(fomat[:, 0]).index(xval)}, {len(y_smo)}')
        ytestval = y_smo[list(fomat[:, 0]).index(xval) - 1]
    smoothmessage = f'{label}      , SmoothingNotComplete!, {yval:0.2e}, {ytestval:0.2e}'
    try:
        if math.log10(ytestval) - math.log10(yval) > 0.05:
            print(smoothmessage)
    except ValueError:
        print(smoothmessage)

    if spec:
        xvals, yvals = fomat[:,0]*uconv[unit], fomat[:,1]
        yvals = np.array([math.log10(abs(max(1, i))) for i in yvals])
        y_smo = np.array([math.log10(abs(max(1, i))) for i in y_smo])
        if onefig:
            fig = plt.figure('knr/kic', figsize=[4,3])
            plt.plot(xvals, y_smo, linewidth=lnsz, alpha=0.5, color='r')  # smooth
            plt.plot(xvals, yvals, linewidth=lnsz, alpha=0.8, label=label)  # kic
        else:
            fig = plt.figure(label, figsize=[4,3])
            # returns log(kic), except if kic is < 1 (negative), then 0
            plt.plot(xvals, yvals, linewidth=lnsz, alpha=0.8, color='k')  # kic
            plt.plot(xvals, y_smo, linewidth=lnsz, alpha=0.5, color='r')  # smooth
        plt.plot(ead, math.log10(yval), 'X', color='k')
        fig.tight_layout()
    return yval


def genspec(specfile, unit='ev', axis=None, onefig=False):
    label = str(specfile.parent.relative_to(Path.cwd()))
    if onefig:
        plt.figure('Abs-Emi', figsize=(4, 3))
    else:
        plt.figure(label, figsize=(4, 3))
    specmat = np.genfromtxt(specfile, delimiter="")
    specmat[:, 1] *= 1 / max(specmat[:, 1])
    k = uconv[unit]
    if unit == 'nm':
        specmat[:, 0] = np.reciprocal(specmat[:, 0], where=specmat[:, 0] != 0)
        if axis is None:
            plt.axis([250, 950, 0, 1])
    if axis is not None:
        plt.axis([axis[0], axis[1], 0, 1])
    specmat[:, 0] *= k
    # if onefig:
    plt.plot(specmat[:, 0], specmat[:, 1], linewidth=lnsz, alpha=0.8, label=label)
    plt.xlabel(unit, fontsize=fntsz)
    # plt.ylabel('Intensity', fontsize=fntsz)
    plt.tight_layout()
    # plt.savefig('/home/koen/un2/mmp/tmp.png')

def inf_main(flname, prop, specargs, kicspecargs):
    datdic = getinp(flname)
    if prop in ['EMI', 'IC', 'NR0']:
        rt = rates(flname, prop)
        if rt is None:
            rt = '  ---  '
            print(f'Error: No rates in file? {flname.relative_to(Path.cwd())}')
    else:
        rt = '         '
    datdic['rtsfsp'] = '       '
    if prop in ['IC', 'NR0']:
        plotfile = [y for y in flname.parent.glob('k??_vs_Ead_T?.dat')][0]
        datdic['rtsfsp'] = rts_from_spec(plotfile, datdic['Ead'] * 27.212, **kicspecargs)
    elif prop in ['OPA', 'EMI'] and specargs['spec']:
        plotfile = [y for y in flname.parent.glob('spec_Int_T?.dat')][0]
        r = dict(specargs)
        del r['spec']
        genspec(plotfile, **r)

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
