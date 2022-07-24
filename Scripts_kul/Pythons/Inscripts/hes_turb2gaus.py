#!/usr/bin/env python3
import argparse
import re
import cmath
import numpy as np
from pathlib import Path
import subprocess

# it's crappy, but it works
b2a=0.529177249

print('not finished? be careful when using, it probably doesnt wotk properly')

def init():
    man = '''
        Extracts lower triangle hessian from turbomole hessian-file.
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=man)
    parser.add_argument("hesfile", help="add hessian file (also used for atnum)")
    parser.add_argument("-g", "--gradfile", help="add gradient file and output gradient or coord")
    parser.add_argument("-a", "--atnum", help="outputs number of atoms instead of hessian", action="store_true")
    parser.add_argument("-x", "--xyzfile", help="outputs xyz instead of gradient", action="store_true")
    parser.add_argument("-p", "--projected", help="Use projected hessian", action="store_true")
    args = parser.parse_args()
    hesfile = Path(args.hesfile).expanduser().absolute()
    gradfile = args.gradfile
    if args.gradfile is not None:
        gradfile = Path(gradfile).expanduser().absolute()
        if not gradfile.is_file():
            print('file not found')
            exit(1)
    if not hesfile.is_file():
        print('file not found')
        exit(1)
    main(hesfile, a=args.atnum, proj=args.projected, g=gradfile, x=args.xyzfile)


def fl2hes(filename, proj=False):
    if proj:
        srch = r'^\$hessian \(projected\)'
    else:
        srch = r'^\$hessian$'
    hes_flag = False
    hi = 0
    hj = 0
    hesline = []
    hesmat = []
    with open(filename, "r") as fl:
        for line in fl.readlines():
            if hes_flag:
                try:
                    lnlst = [float(i) for i in line.split()]
                except ValueError:
                    hesmat.append(hesline)
                    break
                if hi < lnlst[0]:
                    if hesline != []:
                        hesmat.append(hesline)
                        hesline = []
                        hj = 0
                    hi = lnlst[0]
                if hj < lnlst[1]:
                    hj = lnlst[1]
                    [hesline.append(elem) for elem in lnlst[2:]]
            if re.search(srch, line):
                hes_flag = True
                hesline = []
                hesmat = []
        if hesmat == []:
            print('Error matrix is empty')
            exit(1)
        hes_mat = np.array(hesmat)
        hes_tril = hes_mat[np.tril_indices_from(hes_mat)]
        if not np.array_equal(np.tril(hes_mat),  np.tril(hes_mat.transpose())):
            print('Matrix not symmetric! what did you do?!')
            exit(1)
        if len(hes_mat) != int(hi) or int((hi**2+hi)/2) != len(hes_tril):
            print('Error: something weird with length matrix')
            print(len(hes_mat), int(hi), len(hes_tril))
            exit(1)
        if int(hi/3)*3 != hi:
            print('Hessian not 3N matrix, number of atoms no integer')
            exit(1)
        # w, v = (np.linalg.eig(hes_mat))
        # w.sort()
        # # w = [round(cmath.sqrt(i)) for i in w]
        # eigvals2 = np.diagonal(np.dot(np.dot(np.transpose(v), hes_mat), v))
        # print(eigvals2)
        return int(hi/3), hes_tril


def fl2coordgrad(filename, nat):
    script = f"tail -n{nat*2+1} {filename} | head -n-1 | sed 's/D/E/g'"
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    inflist = [elems.decode('utf8').split() for elems in p.stdout.readlines()]
    coordmat = np.array(inflist[0:nat])
    xyz = coordmat[:, 0:3].astype(float)*b2a
    xyzmat = np.column_stack((coordmat[:, 3], xyz))
    gradmat = np.array(inflist[nat:])
    return gradmat, xyzmat


def main(filename, a=False, proj=False, g=False, x=False):
    at, hes = fl2hes(filename, proj)
    if a:
        print(at)
    elif x:
        grad, xyz = fl2coordgrad(g, at)
        [print(*line) for line in xyz]
    elif g:
        grad, xyz = fl2coordgrad(g, at)
        [print(*line) for line in grad]
    else:
        print(*hes)


if __name__ == '__main__':
    init()
    # fl = Path('~/Documents/Calc/mar/bp/turbopt/f1101/hessian').expanduser().absolute()
    # fl2hes(fl,True)
