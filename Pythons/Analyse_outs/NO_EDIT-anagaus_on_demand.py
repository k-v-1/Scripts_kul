import os
import subprocess
from itertools import chain
import re
import numpy as np
import argparse
import csv


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument("dirname", help="Give name of directory with Gaussian output files")
    args = parser.parse_args()
    if args.dirname[0] in ('/', '~'):
        dirname = args.dirname
    else:
        dirname = os.getcwd() + '/' + args.dirname
    if dirname[-1] != '/':
        dirname = dirname+'/'
    main(dirname)


def catgreptail(filename, *inlist):
    # cat $filename | grep -A$inlist[1]-1 "$inlist[0]" | tail -n inlist[1]
    # cat gr3101.gjf.log | grep -A3 "Excited State   1"| tail -n 4
    t = []
    for inlst in inlist:
        gnum = inlst[1]
        gsearch = inlst[0]
        script = """
        cat %s | grep -A%d "%s" | tail -n %d
        """ % (filename, gnum - 1, gsearch, gnum)
        p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        t.append([i.decode('utf8').replace('>', ' ').split() for i in p.stdout.readlines()])
    return t


def get_info(mapname, filename, es):
    if es == 0:
        txf = catgreptail(mapname + filename, ['Zero-point correction', 5])
    else:
        linum = 1
        txf = catgreptail(mapname + filename, ['Excited State   %d' % es, linum])
        while str(es+1)+':' not in chain(*chain(*txf)) and "selected" not in chain(*chain(*txf)) and linum < 15:
            # Not working if too many contributions (10)
            linum = linum + 1
            txf = catgreptail(mapname + filename, ['Excited State   %d' % es, linum])
        if 'Copying' in chain(*chain(*txf)):
            linum = linum - 3
        txf = catgreptail(mapname + filename, ['Excited State   %d' % es, linum], ['Zero-point correction', 5])
    spl_txf = []
    for i in range(len(txf)):
        spl_txf.append(txf[i])
    return spl_txf  # gives list of 2 big lists: [[ES-part],[GS-part]], both are lists-of-lists


def nfo2mat(genmap, genfile, esnum):
    mat1ix = [get_info(genmap, genfile, esnum)][0]
    # print(mat1ix)
    # print(esnum)
    mat3ix = []
    temp0 = mat1ix[0]  # For ESs, this is the excitation part, for gs, this is the zpe-part
    if 'Excited' in chain(*mat1ix[0]):
        temp1 = mat1ix[1]  # zpe-part for ESs
        if temp1 == []:
            mat2ix = [genfile.split('.')[0], [0, 0], [temp0[0][4], temp0[0][8].split('=')[1], temp0[-1][4]]]
        else:
            mat2ix = [genfile.split('.')[0], [temp1[4][6], temp1[0][2]], [temp0[0][4], temp0[0][8].split('=')[1], temp0[-1][4]]]
        for j in range(1, len(temp0)-2):  # Get all the i→f
            temp = []
            for k in [0, 2, 3]:
                temp.append(temp0[j][k])
            mat2ix.append(temp)
    else:
        mat2ix = [genfile.split('.')[0], temp0[4][6], temp0[0][2]]

    mat3ix.append(mat2ix)
    return mat3ix


def n2m2fc(genmap, genfile, esnum=1):
    script = """
            grep "Excited State   " %s | tail -n1
            """ % (genmap+genfile)
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    esmax = int(p.stdout.readline().decode('utf8').split()[2].split(':')[0])
    for es in range(esnum, esmax+1):
        fullmat = nfo2mat(genmap, genfile, es)[0]
        # print(fullmat)
        pmat = [fullmat[2][0], fullmat[2][1], fullmat[3:]]  # if not es==esmax else fullmat[3:-4]]
        print(genfile.split('.')[0]+'#'+str(es), pmat[0], pmat[1], *np.hstack(pmat[2]))


def detes(filename):
    script = """
            grep -A4 "This state for optimization and" %s | tail -n1
            """ % filename
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    inputline = p.stdout.readline().decode('utf8')
    try:
        esnum = int(inputline[inputline.find('Excited')+16]) - 1  # better change find to split?
    except IndexError:
        esnum = 0
    return esnum


def checkimag(filename):
    chk = catgreptail(filename, ['imaginary', 1])
    if chk[0]:
        print(os.path.basename(filename), *chk[0][0])


def main(allmap):
    files_all = os.listdir(allmap)
    files_all.sort()
    nfind = ['Name', ['EE+ZPE', 'ZPE'], ['emmE-eV', 'f', 'ESE'], ['i →f, coef']]
    print(*np.hstack(nfind))
    # with open(allmap+'mycsv.csv', 'w', newline='') as f:
    #     thewriter = csv.writer(f)
    #     thewriter.writerow(np.hstack(nfind))
    for allvar in files_all:

        try:
            # if re.search("bapr[12].._2[.]gjf[.]log", allvar):
            # if re.search("wdh....[.]gjf[.]log", allvar):
            # if re.search("grt[13456].0.F.C[.]gjf[.]log", allvar):
            if re.search("[fF][cC].*[.]log", allvar):
                if catgreptail(allmap + allvar, ['Elapsed', 2]) == [[]]:
                    print("Calc not finished")
                else:
                    n2m2fc(allmap, allvar)
            elif re.search("[.]log", allvar):
                if catgreptail(allmap + allvar, ['Elapsed', 2]) == [[]]:
                    print("Calc not finished")
                else:
                    checkimag(allmap+allvar)
                    num2 = detes(allmap+allvar)
                    nfo = nfo2mat(allmap, allvar, num2)
                    print(*np.hstack(nfo[0]))
        except IndexError:
            print('indexerror  ' + allvar + '-->WrongFreqCalc?')


if __name__ == '__main__':
    # workdir = "/home/r0584198/Documents/Calc/azuder/gaus/"
    # workdir = "/home/r0584198/Documents/Calc/un/preps/freq-vt1/"
    # workdir = "/home/u0133458/Documents/Calc/dav/"
    # workdir = "/home/u0133458/Documents/Calc/wdh/flipi/g_thf/"
    # workdir = "/home/u0133458/Documents/Calc/wdh/wdh_old/"
    # workdir = "/home/u0133458/Documents/Calc/bapr2021/q5wh/"
    # main(workdir)
    init()
