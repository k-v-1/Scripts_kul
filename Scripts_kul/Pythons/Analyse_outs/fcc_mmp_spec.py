#!python3
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
import math
import littlescripts as lts

uconv = {'nm': 1239.849, 'rcm': 8065.5, 'cm-1': 8065.5, 'ev': 1, 'au': 0.0367}
colconv = {'nm': 3, 'rcm': 2, 'cm-1': 2, 'ev': 1, 'au': 0}
fntsz = 10
lnsz = 0.8


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', type=str, nargs='+',
                        help='one or more folders containing {abs,emi}/spec_Int_TD.dat, and/or kic/kic_vs_Ead_TD.dat; '
                             'OR containing kr/spec.tvcf.spec.dat, and/or kic/ic.tvcf.fo.dat')
    parser.add_argument('-1', '--nokic', action='store_true', help='disable plotting of kic')
    parser.add_argument('-2', '--nospec', action='store_true', help='disable plotting of abs/emi')
    parser.add_argument('-l', '--logkic', action='store_true', help='plot log(kic) instead of kic')
    parser.add_argument('-u', '--unit', type=str.lower, help='eV, nm, rcm=cm-1', default='ev')
    parser.add_argument('-a', '--axis', type=float, nargs=2, help='specify x-axis values', default=None)
    args = parser.parse_args()
    for folder in args.folders:
        if folder[0] in ('/', '~'):
            dirgen = folder
        else:
            dirgen = os.getcwd() + '/' + folder
        if dirgen[-1] != '/':
            dirgen += '/'

        dirabs = dirgen + 'abs/'
        diremi = dirgen + 'emi/'
        dirkic = dirgen + 'kic/'
        dirkr = dirgen + 'kr/'

        if not args.nospec:
            try:
                filabs = dirabs + 'spec_Int_TD.dat'
                filemi = diremi + 'spec_Int_TD.dat'
                genspec_temp(filabs, filemi, unit=args.unit, axval=args.axis)
            except OSError or FileNotFoundError:
                try:
                    filkr = dirkr + 'spec.tvcf.spec.dat'
                    genspec_mmp(filkr, unit=args.unit, axval=args.axis)
                except OSError or FileNotFoundError:
                    plt.close()
                    print('no spectra in folder')
        if not args.nokic:
            try:
                filkic = dirkic + 'kic_vs_Ead_TD.dat'
                genkicspec(filkic, p1='fcc', unit=args.unit, axval=args.axis, klog=args.logkic)
            except (OSError, FileNotFoundError):
                try:
                    filkic = dirkic + 'ic.tvcf.fo.dat'
                    genkicspec(filkic, p1='mmp', unit=args.unit, axval=args.axis, klog=args.logkic)
                except (OSError or FileNotFoundError):
                    plt.close()
                    print('no ic-file found')
    plt.show()


def genkicspec(filkic, p1, unit='ev', axval=None, klog=False, ead_kic=None):
    plt.figure(filkic.split('/')[-3] + ' - ic', figsize=(4, 3))
    matkic = np.genfromtxt(filkic, delimiter="")
    if p1 == 'fcc':
        xvals, yvals = matkic[:, 0] * uconv[unit], matkic[:, 1]
        if unit == 'nm':  # This doesn't make much sense actually
            xvals = np.reciprocal(xvals, where=xvals != 0)
            if axval is None:
                plt.xlim(0, 1)
    else:  # p1 == 'mmp':
        xvals, yvals = matkic[:, colconv[unit]], matkic[:, 5]

    y_smo = lts.smooth(yvals, 20)
    if axval is not None:
        plt.xlim(axval[0], axval[1])
    if klog:  # returns log(kic), except if kic is < 1 (negative), then 0
        yvals = np.array([math.log10(abs(max(1, i))) for i in yvals])
        y_smo = np.array([math.log10(abs(max(1, i))) for i in y_smo])
    plt.plot(xvals, yvals, linewidth=lnsz, alpha=0.8, color='k')  # kic
    plt.plot(xvals, y_smo, linewidth=lnsz, alpha=0.5, color='r')  # smooth
    if ead_kic is not None:  # Todo, not used yet
        for i in range(0, len(ead_kic), 2):
            plt.plot(ead_kic[i], ead_kic[i + 1], ['X', 'x'][i // 2 % 2], color='k')

    plt.xlabel(unit, fontsize=fntsz)
    plt.ylabel('kic', fontsize=fntsz)
    plt.tight_layout()
    # plt.savefig('/home/koen/un2/mmp/tmp.png')


def genspec_temp(filabs, filemi, unit='ev', axval=None):
    plt.figure(filabs.split('/')[-3], figsize=(4, 3))
    matabs = np.genfromtxt(filabs, delimiter="")
    matabs[:, 1] *= 1 / max(matabs[:, 1])
    matemi = np.genfromtxt(filemi, delimiter="")
    matemi[:, 1] *= 1 / max(matemi[:, 1])
    k = uconv[unit]
    if unit == 'nm':
        matabs[:, 0] = np.reciprocal(matabs[:, 0], where=matabs[:, 0] != 0)
        matemi[:, 0] = np.reciprocal(matemi[:, 0], where=matemi[:, 0] != 0)
        if axval is None:
            plt.axis([250, 950, 0, 1])
    if axval is not None:
        plt.axis([axval[0], axval[1], 0, 1])
    matabs[:, 0] *= k
    matemi[:, 0] *= k
    plt.plot(matabs[:, 0], matabs[:, 1], linewidth=lnsz, alpha=0.8, color='blue')  # abs
    plt.plot(matemi[:, 0], matemi[:, 1], linewidth=lnsz, alpha=0.8, color='green')  # emi
    plt.xlabel(unit, fontsize=fntsz)
    plt.ylabel('Intensity', fontsize=fntsz)
    plt.tight_layout()
    # plt.savefig('/home/koen/un2/mmp/tmp.png')


def genspec_mmp(filename, unit='ev', axval=None):
    plt.figure(filename.split('/')[-3], figsize=(4, 3))
    if axval is not None:
        plt.axis([axval[0], axval[1], 0, 1])
    rspmat = np.genfromtxt(filename, delimiter="")
    k = colconv[unit]
    plt.plot(rspmat[:, k], rspmat[:, 4], linewidth=lnsz, alpha=0.8, color='blue')  # abs
    plt.plot(rspmat[:, k], rspmat[:, 5], linewidth=lnsz, alpha=0.8, color='green')  # emi
    # plt.plot(rspmat[:, k], rspmat[:, 6], linewidth=1.5, alpha=0.5, color='black')
    plt.xlabel(unit, fontsize=fntsz)
    plt.ylabel('Intensity', fontsize=fntsz)
    plt.tight_layout()


if __name__ == '__main__':
    init()
