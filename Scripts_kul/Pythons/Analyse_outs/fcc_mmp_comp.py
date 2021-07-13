#!python3
import argparse
import os
import re
import matplotlib.pyplot as plt
import numpy as np
import math
import subprocess
import copy as cp

# uconv = {'nm': 1239.849, 'rcm': 8065.5, 'cm-1': 8065.5, 'ev': 1}
# colconv = {'nm': 3, 'rcm': 2, 'cm-1': 2, 'ev': 1}
fntsz = 10
lnsz = 0.8


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', type=str, nargs='+',
                        help='even number of folders containing 1) evc.cart/dint.dat and 2) ?/duschinksy.dat')
    parser.add_argument('-1', '--noinfo', action='store_true', help='disable general information')
    parser.add_argument('-d', '--dus', action='store_true', help='Compare Duschinsky information')
    parser.add_argument('-H', '--HR', action='store_true', help='Compare Huang-Rhys factors')
    parser.add_argument('-p', '--noplot', action='store_true', help='disable plotting')
    # parser.add_argument('-u', '--unit', type=str.lower, help='eV, nm, rcm=cm-1', default='ev')
    # parser.add_argument('-a', '--axis', type=float, nargs=2, help='specify x-axis values', default=None)
    args = parser.parse_args()

    def getfl(folder):
        prog = None
        if folder[0] in ('/', '~'):
            drg = folder
        else:
            drg = os.getcwd() + '/' + folder
        if drg[-1] != '/':
            drg += '/'
        if re.search('evc[.](cart|dint)[.]dat', str(os.listdir(drg))):
            prog = 'mmp'
        elif re.search('(abs|emi|kic)', str(os.listdir(drg))):
            prog = 'fcc'
        return drg, prog

    for ix in range(len(args.folders) // 2):
        name1 = args.folders[2 * ix]
        name2 = args.folders[2 * ix + 1]
        try:
            drg1, prg1 = getfl(name1)
            drg2, prg2 = getfl(name2)
        except FileNotFoundError:
            print('Error: Filenotfound; Calculation not according to name-conventions or not finished correctly?')
            print('skipping following directories: %s and %s' % (name1, name2))
            continue
        if not args.noinfo:
            print('==> ' + name1)
            inf_main(drg1, prg1)
            print('\n==> ' + name2)
            inf_main(drg2, prg2)
        if args.HR:
            plt.figure('hr1 - hr2 ' + str(ix), figsize=(8, 2.5))
            hr_main(drg1, drg2, p1=prg1, p2=prg2)
        if args.dus:
            plt.figure('dus1 - dus2 - abs. diff.' + str(ix), figsize=(8, 2.5))
            dus_main(drg1, drg2, p1=prg1, p2=prg2)
        print('-=' * 25)
    if not args.noplot:
        plt.show()
    else:
        plt.close('all')


def inf_main(d1, p1='mmp'):
    def rates():
        script = ''
        if p1 == 'fcc':
            script = """
                        cat %s/*/*.out | grep "kr(s-1) =" | awk '{print $3}'
                        cat %s/*/*.out | grep "IC rate constant (s-1)" | awk '{print $5}'
                        """ % (d1, d1)
        elif p1 == 'mmp':
            script = """
                        cat %s/*/spec.tvcf.log | grep "radiative rate" | awk '{print $5}'
                        tail -n1 %s/*/ic.tvcf.log | awk '{print $6}'
                        """ % (d1, d1)
        p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        return [float(line.decode('utf8')) for line in p.stdout.readlines()]

    def times():
        if p1 == 'fcc':
            script = """
                        grep "CPU (s)   " %s/{abs,emi,kic}/*.out | awk '{print $4}'
                        """ % d1
            p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
            # print(p.stdout.readline().decode('utf8'))
            # tms = [int(elem) for elem in p.stdout.readline().decode('utf8')]
            tms = [float(line.decode('utf8')) for line in p.stdout.readlines()]
            print('tabs = %d; temi = %d; tkic = %d; tot = %d' % (tms[0], tms[1], tms[2], sum(tms)))
        elif p1 == 'mmp':
            print('No time printed in MOMAP')

    try:
        times()
    except IndexError:
        print('Error: No time in file?')
    try:
        rts = rates()
        print('kr = %.2e\nkic = %.2e' % (rts[0], rts[1]))
    except IndexError:
        print('Error: No rates in file?')
    # todo: add info about number of points, broadening, etc.?


def hr_main(d1, d2, p1='mmp', p2='fcc'):
    # HR = 0.5 * dimshift**2. Attention, in fcc, modes aren't always in order of energy
    # HR in fcc-HR file are from 1st state only! --> get from outfile
    # getfunctions return np-matrix with freq0-hr0-freq1-hr1 (resp S0, S1) as rows
    def get_hr_mmp(folder, cdvar='cart', state=0):
        flname = folder + 'evc.' + cdvar + '.dat'
        lines = []
        with open(flname, "r") as fl:
            startval = 10000
            for i, line in enumerate(fl.readlines()):
                if re.search('====================================', line):
                    startval = i + 3
                if startval <= i:
                    if re.search('-----------', line):
                        endval = i
                        break
                    lines.append([float(y.replace('A', '0.00')) for y in line.split()])
        with open(flname, "r") as fl:
            for i, line in enumerate(fl.readlines()):
                if i == endval + 1:
                    retots = [float(line.split()[4]), float(line.split()[5])]
        lines = np.array(lines)
        data = np.array([lines[:, 3], lines[:, 6], lines[:, 9], lines[:, 12]])
        dif1, dif2 = round(sum(lines[:, 7])) - round(retots[0]), round(sum(lines[:, 13])) - round(retots[1])
        if abs(dif1) > 1 or abs(dif2) > 1:
            print(flname, 'ERROR, sum not equal to total RE!!', dif1, dif2)
        return data

    def get_hr_fcc(folder, state=0):
        def matprep(lines):
            mat = np.vstack([np.zeros((6,3)), np.delete(np.array(lines), 0, 1)])
            mat = mat[mat[:, 0].argsort()]
            for i in range(len(mat[:,2])):
                mat[i,2] = 0.5*mat[i,2]**2
            return mat[:,1:]

        def outfl2mat(flname):
            lines, lines1 = [], []
            saveflag = False
            with open(flname, "r") as fl:
                for line in fl.readlines():
                    if saveflag:
                        try:
                            if line.split()[0] == 'IND':
                                continue
                        except IndexError:
                            if not lines1:
                                lines1 = cp.deepcopy(lines)
                                lines = []
                            else:
                                lines2 = cp.deepcopy(lines)
                            saveflag = False
                            continue
                        lines.append([float(y) for y in line.split()])
                    if re.search("MODES SORTED BY DECREASING DIMENSIONLESS SHIFT", line):
                        saveflag = True
            return np.hstack([matprep(lines1), matprep(lines2)]).transpose()

        def get_raw():
            for pref in ['/', 'kic/', 'emi/', 'abs/']:
                try:
                    return outfl2mat(folder + pref + 'fcc_' + pref[:-1] + '.out')
                except OSError or FileNotFoundError:
                    pass
            print('*out.dat not found')

        return get_raw()

    def comp_hr(freqhuang1, freqhuang2):  # compares HR matrices
        # print min, max, avg, stdv of hrdiff
        frhrdiff = freqhuang2 - freqhuang1
        if abs(min(frhrdiff[[0,2],:].ravel())) + max(frhrdiff[[0,2],:].ravel()) > 0.1:
            print('!!\nWarning: frequencies may differ!')
        print('statistics of the difference matrix (mmp only prints until 1E-4)')
        print('S0: min: %.1e ; max: %.1e; std: %.1e' % (np.min(frhrdiff[1]), np.max(frhrdiff[1]), np.std(frhrdiff[1])))
        print('S1: min: %.1e ; max: %.1e; std: %.1e' % (np.min(frhrdiff[3]), np.max(frhrdiff[3]), np.std(frhrdiff[3])))
        # plot hr-factors for gs and es
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212)
        for i in 0, 1:
            ax = [ax1, ax2][i]
            ax.plot(freqhuang1[2*i], freqhuang1[2*i+1], '.k', markersize=8)
            ax.vlines(freqhuang1[2*i], 0, freqhuang1[2*i+1], 'k')
            ax.plot(freqhuang2[2*i], freqhuang2[2*i+1], '+r', markersize=8)
            ax.vlines(freqhuang2[2*i], 0, freqhuang2[2*i+1], 'r', linestyles='dotted')
        plt.tight_layout()

    if p1 == 'mmp':
        frhr1 = get_hr_mmp(d1)
    elif p1 == 'fcc':
        frhr1 = get_hr_fcc(d1)
    else:
        print('wrong hr-program input')
        plt.close()
        return
    if p2 == 'mmp':
        frhr2 = get_hr_mmp(d2)
    elif p2 == 'fcc':
        frhr2 = get_hr_fcc(d2)
    else:
        print('wrong hr-program input')
        plt.close()
        return
    comp_hr(frhr1,frhr2)


def dus_main(d1, d2, p1='mmp', p2='fcc'):
    # Converts column or square matrix into sq (default) or col (conv=2c)
    # Possible to add or remove first 6 rows&cols
    def c2m2c(mat, conv='2m', add6=False, rem6=False):  # conv = 2c or 2m
        def c2m(m):
            return m.reshape(int(math.sqrt(len(m))), int(math.sqrt(len(m))))

        def m2c(m):
            return mat.reshape(mat.size, )

        if len(mat.shape) == 1:
            mat2 = c2m(mat)
        elif len(mat.shape) == 2:
            mat2 = mat
        else:
            print('Error in matrix-column conversion')
            return mat
        if add6:
            B = np.zeros([6, len(mat2)])
            C = np.zeros([len(mat2) + 6, 6])
            mat2 = np.hstack([C, np.vstack([B, mat2])])
        if rem6:
            mat2 = np.delete(np.delete(mat2, range(6), 1), range(6), 0)
        if conv == '2c':
            mat2 = m2c(mat2)
        return mat2

    # Both get_dus_mmp/fcc give 3n*3n numpy-matrix (incl transrot)
    def get_dus_mmp(folder, cdvar='cart'):
        flname = folder + 'evc.' + cdvar + '.dat'
        with open(flname, "r") as fl:
            d_elem1 = []
            d_elem2 = []
            dflag = False
            d2 = False
            for line in fl.readlines():
                if dflag:
                    if re.search('MODE', line):
                        continue
                    elif re.search('[-]{10}', line):
                        d2 = True
                        dflag = False
                        continue
                    if d2:
                        [d_elem2.append(float(elem)) for elem in line.split()]
                    else:
                        [d_elem1.append(float(elem)) for elem in line.split()]
                if re.search('MODE {4}', line):
                    dflag = True
        return c2m2c(np.array(d_elem1)), c2m2c(np.array(d_elem2))

    def get_dus_fcc(folder):
        def get_raw():
            for pref in ['/', 'kic/', 'emi/', 'abs/']:
                try:
                    return np.genfromtxt(folder + pref + 'duschinsky.dat')
                except OSError or FileNotFoundError:
                    pass
            print('duschinsky.dat not found')

        matexp = c2m2c(get_raw(), add6=True)
        return matexp

    def comp_dus(dus1, dus2, filename='duscomp.dat'):  # compares duschinsky matrices (square)
        dusdiff = np.absolute(dus1) - np.absolute(dus2)
        dusdiff_6 = c2m2c(dusdiff, rem6=True)
        # create output file with dus1, dus2 and dusdiff
        duscomb = np.vstack((dus1, np.ones(len(dus1)), dus2, np.ones(len(dus1)), dusdiff))
        # np.savetxt(filename, duscomb, fmt="%1.3f", delimiter=' ')
        # print min, max, avg, stdv of dusdiff with and without 6transrots
        print('statistics of the absolute difference matrix')
        print('min: %.1e ; max: %.1e; std: %.1e' % (np.min(dusdiff), np.max(dusdiff), np.std(dusdiff)))
        print('statistics of the absolute difference matrix, without the first 6 trans/rot elements')
        print('min: %.1e ; max: %.1e; std: %.1e' % (np.min(dusdiff_6), np.max(dusdiff_6), np.std(dusdiff_6)))
        # display colormap of dus1, dus2 and dusdiff (matplotlib subplots)
        plt.pcolormesh(duscomb.transpose(),
                       cmap='twilight_shifted')  # seismic, PiYG [diverging], twilight_shifted [cyclic]
        tcklst = [np.min(duscomb), np.min(duscomb) / 2, 0, np.max(duscomb) / 2, np.max(duscomb)]
        cb = plt.colorbar(orientation='vertical', ticks=tcklst)
        cb.set_ticklabels([round(tck, 1) for tck in tcklst])
        plt.xlabel('S$_0$ modes')
        l = len(dus1)
        plt.xticks([0, l // 2, l + 1, 1 + 3 * l // 2, 2 * l + 2, 2 + 5 * l // 2], [0, l // 2, 0, l // 2, 0, l // 2])
        plt.yticks([0, l // 2])
        plt.ylabel('S$_1$ modes')
        plt.tight_layout()

    if p1 == 'mmp':
        dus1 = get_dus_mmp(d1)[0]
    elif p1 == 'fcc':
        dus1 = get_dus_fcc(d1)
    else:
        print('wrong dus-program input')
        plt.close()
        return
    if p2 == 'mmp':
        dus2 = get_dus_mmp(d2)[0]
    elif p2 == 'fcc':
        dus2 = get_dus_fcc(d2)
    else:
        print('wrong dus-program input')
        plt.close()
        return
    comp_dus(dus1, dus2)


if __name__ == '__main__':
    init()
