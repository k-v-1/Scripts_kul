#!/usr/bin/env python3


#not usefull, taking derivatives in xyz is shitty anyway :p
##
#
exit(0)



import argparse
from pathlib import Path
import sys
import numpy as np
from copy import deepcopy

def init():
    # Give .xyz-basefile, dif (displacment value delta) in default Angstorm
    parser=argparse.ArgumentParser(description="""generate displaced xyz files
    for finite difference""")
    parser.add_argument('xyz_file')
    parser.add_argument('-d', '--dif', type=float, required=False, default=0.001)
    parser.add_argument('-u', '--unit', required=False, default="A")
    parser.add_argument("-t", "--header", action="store_true",
                        help="adds the total number of atoms + title as 2-line-header of xyz-file")
    args=parser.parse_args()

    xyz_in      = Path(args.xyz_file).expanduser().absolute()
    delta       = float(args.dif)
    unit        = args.unit
    header      = args.header

    if not xyz_in.is_file():
        print(f'{xyz_in} not found', file=sys.stderr)
        sys.exit(1)
    if unit=="A":
        delta*=1
    else:
        print("Finish the unit-conversion in program!", file=sys.stderr)
        sys.exit(1)

    init_coords = file2mat(xyz_in)
    mat2files(init_coords, xyz_in, delta, header=header)

def file2mat(infile):
    coordarr = []
    with open(infile, 'r') as fin:
        for line in fin:
            if len(line.rstrip().split()) == 4:
                coordarr.append(line.split())
    return coordarr

def mat2files(cinit, infile, diff, header=False):
    nat = len(cinit)
    for k in range(nat):
        for i in range(6):
            filedest = infile.parent / f"{infile.stem}_{k+1}{['xp','xm','yp','ym','zp','zm'][i]}.xyz"
            cnew = deepcopy(cinit)
            cnew[k][i//2+1] = f'{float(cinit[k][i//2+1]) + diff*(-1)**i:.10f}'
            with open(filedest, 'w') as fout:
                if header:
                    fout.write(f'{nat}\n')
                    fout.write('title\n')
                for l in range(nat):
                    fout.write(f'{cnew[l][0]} {cnew[l][1]} {cnew[l][2]} {cnew[l][3]}\n')

if __name__ == '__main__':
    init()
