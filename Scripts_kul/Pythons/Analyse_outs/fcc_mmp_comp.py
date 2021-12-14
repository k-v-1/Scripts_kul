#!python3
import argparse
from pathlib import Path
import re
import matplotlib.pyplot as plt
import numpy as np
import math
import subprocess
import copy as cp
import littlescripts as lts

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
    parser.add_argument('-i', '--info', action='store_true', help='Show only in&output information')
    # parser.add_argument('-u', '--unit', type=str.lower, help='eV, nm, rcm=cm-1', default='ev')
    # parser.add_argument('-a', '--axis', type=float, nargs=2, help='specify x-axis values', default=None)
    args = parser.parse_args()

    # TODO: Check all files on content and determine like this what filename to use for data obtaining
    def getfl(folder):
        fldr_lst = str(list(Path(Path(folder).expanduser().absolute()).glob('./*')))
        if re.search('evc[.](cart|dint)[.]dat', fldr_lst):
            prog = 'mmp'
        elif re.search('(abs|emi|kic)', fldr_lst):
            prog = 'fcc'
        else:
            print('error')  # todo write error: err=1 --> if err==1; print...
            prog = None
        return prog

    header = True
    if args.info:
        for name in args.folders:
            drg = Path(name).expanduser().absolute()
            if not drg.is_dir():
                continue  # TODO: More checks!
            prg = getfl(drg)
            if header:
                print('name, kr (s-1), kic(s-1), Temp (K), Ead (eV), tmax-ic (fs), dt-ic (fs), points-ic, lor/gau, '
                      'FWHM (rcm), time/freq, time (s)')
                header = False
            inf_main(drg, prg, linear=True)
            # except (FileNotFoundError, NotADirectoryError, OSError):
            # except (FileNotFoundError, KeyError, NotADirectoryError):
            # print(
            #     'Error: Filenotfound; %s-Calculation not according to name-conventions '
            #     'or not finished correctly?' % name)
            # print('skipping following directory: %s' % name)
            # continue
        exit(0)

    # should only be accesible if no args.info
    for ix in range(len(args.folders) // 2):
        name1 = args.folders[2 * ix]
        drg1 = Path(name1).expanduser().absolute()
        name2 = args.folders[2 * ix + 1]
        drg2 = Path(name2).expanduser().absolute()
        try:
            prg1 = getfl(name1)
            prg2 = getfl(name2)
        except (FileNotFoundError, KeyError, NotADirectoryError):
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


def inf_main(d1, p1='mmp', linear=False):
    # t0d0: solve error when file not found (dictionary error?) ==> Solved by catching exception in init()
    def getinp():  # FWHM in a.u.
        script = ''
        infdic = {'Temp': -math.inf, 'Ead': -math.inf, 'tmax:': -math.inf, 'dt': -math.inf, 'points': -math.inf,
                  'isgauss': '-', 'BroadenType': '-', 'FWHM': -math.inf, 'Broadenfunc': '-'}
        if p1 == 'fcc':
            kicout = list(Path(d1).glob('./*[iI][cC]/*.out'))[0]
            script = """
                        cat <<'END' | sh | xargs echo
                        fl=%s
                        grep "Temperature" $fl | awk '{print "Temp",$3}'
                        grep -A1 "ADIABATIC ENERGY" $fl | tail -n1 | awk '{print "Ead", 0.0367484*$1}'
                        # grep "Total time" $fl | awk '{print "tmax",41.341373*$4}'
                        # grep "Time step" $fl | awk '{print "dt",41.341373*$5}'
                        # grep "data points" $fl | awk '{print "points",$5}'
                        grep "tfin  =" $fl | awk '{print "tmax",41.341373*$3}'
                        grep "dt    =" $fl | awk '{print "dt",41.341373*$3}'
                        grep "ntime =" $fl | awk '{print "points",$3}'
                        grep "Broad. function" $fl | awk '{print "BroadenType",$4}'
                        grep -E "HWHM {9}=" $fl | awk '{print "FWHM",2*0.0367485*$3}'
                        grep "Broad. exponent" $fl | awk '{print "brexp", $4}'
END
                        """ % kicout  # Total time, timestep etc not working with TI --> tfin, dt, ntime
        elif p1 == 'mmp':
            script = """grep -E "(Temp|Ead|tmax|dt|isgauss|Broaden.*|FWHM) {15}" %s/kic/ic.tvcf.log | awk '{print $1,
            $3}' | xargs echo""" % d1
        p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        inflist = p.stdout.readline().decode('utf8').split()
        for i in range(len(inflist) // 2):
            try:
                infdic[inflist[2 * i]] = float(inflist[2 * i + 1])
            except ValueError:
                infdic[inflist[2 * i]] = inflist[2 * i + 1]
        return infdic

    def rates():
        if p1 == 'fcc':
            script = """
                        fl=%s
                        tail -n40 $fl/*/*.out | grep "kr(s-1) =" | awk '{print $3}'
                        tail -n40 $fl/*/*.out | grep "IC rate constant (s-1)" | awk '{print $5}'
                        # cat $fl/*/*.out | grep "kr(s-1) =" | awk '{print $3}'
                        # cat $fl/*/*.out | grep "IC rate constant (s-1)" | awk '{print $5}'
                        """ % d1  # Speedup with tail!
        else:  # p1 == 'mmp':
            script = """
                        fl=%s
                        cat $fl/*/spec.tvcf.log | grep "radiative rate" | awk '{print $5}'
                        tail -n1 $fl/*/ic.tvcf.log | awk '{print $6}'
                        """ % d1
        p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        return [float(line.decode('utf8')) for line in p.stdout.readlines()]

    def rts_from_spec(ead, points=10):  # todo: how to choose points?; #todo: Show graph?; .......
        if p1 == 'fcc':
            plotfile = [y for y in d1.glob('kic/kic_vs_Ead_T?.dat')][0]
            fomat = np.genfromtxt(plotfile)
        else:  # p1 == 'mmp':
            fomat = np.genfromtxt(d1 / 'kic/ic.tvcf.fo.dat', delimiter="")
            fomat = fomat[:, [1, 5]]
        fo_smo = lts.smooth(fomat[:, 1], points)
        # fo_smo = fomat[:, 1]
        xval = lts.closest(fomat[:, 0], abs(ead))
        yval = fo_smo[list(fomat[:, 0]).index(xval)]
        try:
            ytestval = fo_smo[list(fomat[:, 0]).index(xval) + 1]
        except IndexError:
            print(f'    kic-val on edge of plotted region? index = {list(fomat[:, 0]).index(xval)} of {len(fo_smo)}')
            ytestval = fo_smo[list(fomat[:, 0]).index(xval) - 1]
        try:
            if math.log10(ytestval) - math.log10(yval) > 0.05:
                print('\n      watch out, smoothing not complete! %0.2e %0.2e' % (yval, ytestval))
        except ValueError:
            print('\n      watch out, smoothing not complete! %0.2e %0.2e' % (yval, ytestval))

        return yval

    def times():
        if p1 == 'fcc':
            script = """
                        tail %s/{abs,emi,kic}/*.out | grep "CPU (s)   " | awk '{print $3}' 
                        """ % d1  # Speeding up with tail!! # no use of f-string, due to {}'s
            p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
            return [float(line.decode('utf8')) for line in p.stdout.readlines()]
        elif p1 == 'mmp':
            return None

    tms = times()
    rts = rates()
    if tms is None:
        tms = [-1] * 3
    try:
        kr, kic = *rts,
    except ValueError:
        kr, kic = 0, 0
        print('Error: No rates in file?')

    if linear:
        datdic = getinp()
        datdic['rtsfsp'] = rts_from_spec(datdic['Ead'] * 27.212)
        if datdic['isgauss'] == '.f.':
            datdic['BroadenType'], datdic['FWHM'], datdic['Broadenfunc'] = '-', '-', '-'
        if re.search('LOR', datdic['BroadenType']):  # more exact fwhm
            datdic['FWHM'] = datdic['brexp'] * 2
        elif re.search('GAU', datdic['BroadenType']):
            datdic['FWHM'] = 2 * math.sqrt(
                2 * datdic['brexp'] / (math.sqrt(2 * math.log10(2))))  # todo: test this expression

        # prntln = '%s, %0.3e, %0.3e, %d, %0.3f, %0.0f, %0.3f, %0.0f, %s, %0.2e, %s, %d, %0.2e' % (
        #     d1.parts[-1], kr, kic, datdic['Temp'], datdic['Ead'] * 27.212, datdic['tmax'] * 0.0241888,
        #     datdic['dt'] * 0.0241888, datdic['points'], datdic['BroadenType'][0:3], datdic['FWHM'] * 219474,
        #     datdic['Broadenfunc'], sum(tms), datdic['rtsfsp'])
        prntln = f"{d1.parts[-1]}, {kr:.3e}, {kic:.3e}, {int(datdic['Temp'])}, {(datdic['Ead'] * 27.212):.3f}," \
                 f" {(datdic['tmax'] * 0.0241888):.0f}, {(datdic['dt'] * 0.0241888):.3f}, {datdic['points']:.0f}," \
                 f" {datdic['BroadenType'][0:3]}, {(datdic['FWHM'] * 219474):.2e}, {datdic['Broadenfunc']}," \
                 f" {int(sum(tms))}, {datdic['rtsfsp']:.2e}"
        if str(datdic['rtsfsp'])[0:2] == str(kic)[0:2]:
            prntln = prntln.rsplit(' ', 1)[0]
        print(prntln.replace('-inf', '-'))

    else:
        # try:
        print('tabs = %d; temi = %d; tkic = %d; tot = %d' % (tms[0], tms[1], tms[2], sum(tms)))
        # print('No time printed in MOMAP')
        # except IndexError:
        #     print('Error: No time in file?')
        try:
            print('kr = %.2e\nkic = %.2e' % (kr, kic))
        except UnboundLocalError:
            print('Error: No rates in file?')


def hr_main(d1, d2, p1='mmp', p2='fcc'):
    # HR = 0.5 * dimshift**2. Attention, in fcc, modes aren't always in order of energy
    # HR in fcc-HR file are from 1st state only! --> get from outfile
    # getfunctions return np-matrix with freq0-hr0-freq1-hr1 (resp S0, S1) as rows
    def get_hr_mmp(folder, cdvar='cart', state=0):
        flname = folder / ('evc.%s.dat' % cdvar)
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
            mat = np.vstack([np.zeros((6, 3)), np.delete(np.array(lines), 0, 1)])
            mat = mat[mat[:, 0].argsort()]
            for i in range(len(mat[:, 2])):
                mat[i, 2] = 0.5 * mat[i, 2] ** 2
            return mat[:, 1:]

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
                        # lines1&2 switched, to get state0 first
                        # to be compliant with newest fcc3.0.1 version
            return np.hstack([matprep(lines2), matprep(lines1)]).transpose()

        def get_raw():
            outfiles = folder.rglob('**/*fcc*.out')
            for fl in outfiles:
                return outfl2mat(fl)
            # for pref in ['', 'kic', 'emi', 'abs']:
            #     try:
            #         return outfl2mat(folder / pref / ('fcc_%s/.out' % pref))
            #     except OSError or FileNotFoundError:
            #         pass
            print('*out.dat not found')

        return get_raw()

    def comp_hr(freqhuang1, freqhuang2):  # compares HR matrices
        # print min, max, avg, stdv of hrdiff
        frhrdiff = freqhuang2 - freqhuang1
        if abs(min(frhrdiff[[0, 2], :].ravel())) + max(frhrdiff[[0, 2], :].ravel()) > 0.1:
            print('!!\nWarning: frequencies may differ!')
        print('statistics of the difference matrix (mmp only prints until 1E-4)')
        print('S0: min: %.1e ; max: %.1e; std: %.1e' % (np.min(frhrdiff[1]), np.max(frhrdiff[1]), np.std(frhrdiff[1])))
        print('S1: min: %.1e ; max: %.1e; std: %.1e' % (np.min(frhrdiff[3]), np.max(frhrdiff[3]), np.std(frhrdiff[3])))
        # plot hr-factors for gs and es
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212)
        for i in 0, 1:
            ax = [ax1, ax2][i]
            ax.plot(freqhuang1[2 * i], freqhuang1[2 * i + 1], '.k', markersize=8)
            ax.vlines(freqhuang1[2 * i], 0, freqhuang1[2 * i + 1], 'k')
            ax.plot(freqhuang2[2 * i], freqhuang2[2 * i + 1], '+r', markersize=8)
            ax.vlines(freqhuang2[2 * i], 0, freqhuang2[2 * i + 1], 'r', linestyles='dotted')
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
    comp_hr(frhr1, frhr2)


def dus_main(d1, d2, p1='mmp', p2='fcc'):
    # Converts column or square matrix into sq (default) or col (conv=2c)
    # Possible to add or remove first 6 rows&cols
    def c2m2c(mat, conv='2m', add6=False, rem6=False):  # conv = 2c or 2m
        def c2m(m):
            return m.reshape(int(math.sqrt(len(m))), int(math.sqrt(len(m))))

        def m2c(m):
            return m.reshape(m.size, )

        if len(mat.shape) == 1:
            mat2 = c2m(mat)
        elif len(mat.shape) == 2:
            mat2 = mat
        else:
            print('Error in matrix-column conversion')
            return mat
        if add6:
            bmat = np.zeros([6, len(mat2)])
            cmat = np.zeros([len(mat2) + 6, 6])
            mat2 = np.hstack([cmat, np.vstack([bmat, mat2])])
        if rem6:
            mat2 = np.delete(np.delete(mat2, range(6), 1), range(6), 0)
        if conv == '2c':
            mat2 = m2c(mat2)
        return mat2

    # Both get_dus_mmp/fcc give 3n*3n numpy-matrix (incl transrot)
    def get_dus_mmp(folder, cdvar='cart'):
        flname = folder / ('evc.%s.dat' % cdvar)
        with open(flname, "r") as fl:
            d_elem1 = []
            d_elem2 = []
            dflag = False
            d2_flg = False
            for line in fl.readlines():
                if dflag:
                    if re.search('MODE', line):
                        continue
                    elif re.search('[-]{10}', line):
                        d2_flg = True
                        dflag = False
                        continue
                    if d2_flg:
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
                    return np.genfromtxt(folder / pref / 'duschinsky.dat')
                except OSError or FileNotFoundError:
                    pass
            print('duschinsky.dat not found')

        matexp = c2m2c(get_raw(), add6=True).transpose()  # Transposed to get state0/1 right (newest fcc-version)
        return matexp

    def comp_dus(mat1, mat2):  # compares duschinsky matrices (square)
        dusdiff = np.absolute(mat1) - np.absolute(mat2)
        dusdiff_6 = c2m2c(dusdiff, rem6=True)
        # create output file with dus1, dus2 (mat1, mat2) and dusdiff
        duscomb = np.vstack((mat1, np.ones(len(mat1)), mat2, np.ones(len(mat1)), dusdiff))
        # np.savetxt(filename, duscomb, fmt="%1.3f", delimiter=' ')
        # print min, max, avg, stdv of dusdiff with and without 6transrots
        print('statistics of the absolute difference matrix')
        print('min: %.1e ; max: %.1e; std: %.1e' % (np.min(dusdiff), np.max(dusdiff), np.std(dusdiff)))
        print('statistics of the absolute difference matrix, without the first 6 trans/rot elements')
        print('min: %.1e ; max: %.1e; std: %.1e' % (np.min(dusdiff_6), np.max(dusdiff_6), np.std(dusdiff_6)))
        # display colormap of dus1, dus2 (mat1,mat2) and dusdiff (matplotlib subplots)
        plt.pcolormesh(duscomb.transpose(),
                       cmap='twilight_shifted')  # seismic, PiYG [diverging], twilight_shifted [cyclic]
        tcklst = [np.min(duscomb), np.min(duscomb) / 2, 0, np.max(duscomb) / 2, np.max(duscomb)]
        cb = plt.colorbar(orientation='vertical', ticks=tcklst)
        cb.set_ticklabels([round(tck, 1) for tck in tcklst])
        plt.xlabel('S$_0$ modes')
        l = len(mat1)
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
    # TEST
    # tstdir = Path('/home/u0133458/sftp/ko/un3/ic2/brt') / 'l0.0001_ti_crt'
    # inf_main(tstdir, p1='fcc',linear=True)

