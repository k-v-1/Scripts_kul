#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import re
import numpy as np
from math import sqrt, ceil
from coordscripts import atnum2sym


def init():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('fchkfiles', type=str, nargs='+',
                        help='fchkfiles to convert to orca\'s .hess file')
    args = parser.parse_args()
    for flstr in args.fchkfiles:
        fchkfl = Path(flstr).expanduser().absolute()
        orcfl = Path(fchkfl.stem + '.hess')  # this way, file will be written in pwd and not in dir of fchkfl. Preference?
        if not fchkfl.is_file():
            print(f'Error: {fchkfl} not found', file=sys.stderr)
            continue
        gnat, gatnums, gcoords, gatweight, hes_full = get_gaus(fchkfl)
        if np.array(hes_full).size == 0:
            print(f'{flstr} no hessian found, not a correct fchk-file?', file=sys.stderr)
            continue

        # writing orca .hess

        with open(orcfl, "w") as f:  # only here opening as w, all others should be a!
            f.write('$orca_hessian_file\n \n$act_atom\n 0\n \n$act_coord\n 0\n \n$act_energy\n   0.000000\n\n')
        orc_hes(orcfl,hes_full)
        # orc_freq(orcfl,gfreqs)
        # orc_nm(orcfl,gvibs)
        orc_coord(orcfl, gatnums, gatweight, gcoords)
        with open(orcfl, 'a') as f:
            f.write('\n\n$end\n\n')


def get_gaus(fchk):  # get information from g16 fchk-file.
    nat=0
    atnums, coords, atweight, hes_full = [], [], [], []
    n3 = 0
    with open(fchk, "r") as f:
        for line in f:  # Don't use f.readlines here, otherwise readline cannot be nested?
            natstr = re.search(r'^Number of atoms +I +([0-9+]+)',line)
            atnumstr = re.search(r'^Atomic numbers +I +N= +([0-9]+)', line) # should be nat
            coordstr = re.search(r'^Current cartesian coordinates +R +N= +([0-9]+)', line) # should be 3*nat
            atweightstr = re.search(r'^Real atomic weights +R +N= +([0-9+]+)',line)
            cfcstr = re.search(r'^Cartesian Force Constants +R +N= +([0-9]+)', line)
            # vibstr = re.search(r'^Vib-Modes +R +N= +([0-9]+)', line) # should be 9*nat*(nat-2)
            if natstr is not None:
                nat = int(natstr.group(1))
            if atnumstr is not None:
                for _ in range(ceil(int(atnumstr.group(1))/6)):
                    for value in f.readline().strip().split():
                        atnums.append(int(value))
            if coordstr is not None:
                for _ in range(ceil(int(coordstr.group(1))/5)):
                    for value in f.readline().strip().split():
                        coords.append(float(value))
            if atweightstr is not None:
                for _ in range(ceil(int(atweightstr.group(1))/5)):
                    for value in f.readline().strip().split():
                        atweight.append(float(value))

            # TODO hopefully not needed
            # Not used, since g16 is not using full 3n*3n, so shape can be 3n*3n-6 or reversed...
            # if vibstr is not None:
            #     vibs=[]
            #     for _ in range(ceil(int(vibstr.group(1))/5)-1):
            #         for value in f.readline().strip().split():
            #             vibs.append(value)
            #     vibmat = np.array(vibs).reshape(())

            if cfcstr is not None:
                row = 0  # row index
                n_el = 0  # number of filled elements in a row
                nelem = int(cfcstr.group(1))
                n3 = int((sqrt(nelem*8+1)-1)/2)
                hes_lowtri = np.zeros((n3,n3))
                for _ in range(ceil(int(cfcstr.group(1))/5)):
                    for value in f.readline().strip().split():
                        if n_el > row:
                            row += 1
                            n_el = 0
                        hes_lowtri[row, n_el] = value
                        n_el += 1
                hes_full = hes_lowtri + hes_lowtri.T - np.diag(np.diag(hes_lowtri))
    # print(nat)
    # print(atnums)
    # print(coords)
    # print(atweight)
    # print(hes_full)
    return nat, atnums, coords, atweight, hes_full


def orc_coord(output, atnumlst, atweightlst, coordlst):  # append BOHR-coordinates to output. Orca format. All inputs in lists.
    nat = len(atnumlst)
    symlst = [atnum2sym[i] for i in atnumlst]  # Angstrom input, bohr output
    coordlst_bohr = [i*0.529177249 for i in coordlst]
    coordmat = np.array(coordlst_bohr).reshape((nat,3))

    with open(output, "a") as f:
        f.write('#\n# The atoms: label  mass x y z (in bohrs)\n#\n$atoms\n')
        f.write(f'{nat}\n')
        for i in range(nat):
            f.write(f' {symlst[i]}   {atweightlst[i]:.8E}')
            [f.write(f' \t{val:.10E}') for val in coordmat[i]]
            f.write('\n')


def orc_hes(output,hes_full):  # append full hessian matrix to output, including title
    n3 = len(hes_full)
    with open(output, "a") as f:
        f.write(f'$hessian\n{n3}\n')
        nrows = ceil(n3/5)  # number of 3n x 5 segments, including last one
        for i in range(nrows):  # first segment is 0
            m5 = min(5, n3-5*i)  # this is 5, except if line is incomplete (last line)

            [f.write(f'                {t+5*i:d}') for t in range(m5)]  # write numbering line
            f.write("\n")
            for j in range(n3):  # write 3n x 5 block: number of row + hessian elements of block
                f.write(f' {j:d}     ')
                [f.write(f' {t:.8E}   ') for t in hes_full[j,5*i:5*i+m5]]
                f.write('\n')
        f.write('\n')


if __name__ == '__main__':
    init()
