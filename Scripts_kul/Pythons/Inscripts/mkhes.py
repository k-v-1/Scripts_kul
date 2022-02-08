import argparse
import os
import re
import numpy as np


def init():
    man = '''
        Extracts hessian from qchem-output.
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=man)
    parser.add_argument("filename", help="add filename")
    parser.add_argument("-a", "--atnum", help="outputs number of atoms instead of hessian", action="store_true")
    args = parser.parse_args()
    if args.filename[0] in ('/', '~'):
        filename = args.filename
    else:
        filename = os.getcwd() + '/' + args.filename

    main(filename, a=args.atnum)


def fl2data(filename):
    atnum_flag = 0
    atnum_array = []
    hes_flag = False
    hi = 0
    hj = 0
    with open(filename, "r") as fl:
        for line in fl.readlines():
            if re.search(r'Standard Nuclear Orientation \(Angstroms\)', line) and atnum_flag == 0:
                atnum_flag = 1
            if atnum_flag > 0:
                if atnum_flag > 3:
                    if re.search("-------------", line):
                        atnum_flag = -1
                    else:
                        atnum_array.append(line.split()[1])
                        atnum = len(atnum_array)
                else:
                    atnum_flag += 1

            if hes_flag:
                if len(line.split()) == 7 or len(line.split()) == 4:
                    if hi >= 3 * atnum:
                        hi = 0
                        hj += 6
                    hes_mat[hi, hj:hj + len(line.split()) -1] = line.split()[1:len(line.split())]
                    hi += 1
                    if hi == 3*atnum and hj > 3*atnum-6:
                        hes_flag = False
                else:
                    pass

            if re.search('Final Hessian', line):
                hes_flag = True
                hes_mat = np.zeros((3 * atnum, 3 * atnum))

            # if re.search("-------- Electric Field --------", line):
            #     te_flag = 1
            # if te_flag > 0:
            #     if te_flag > 3:
            #         if re.search("-------------", line):
            #             te_flag = 0
            #         else:
            #             te_mat.append(line.split()[3:6])
            #     else:
            #         te_flag += 1
    # print(atnum_array)
    hes_tril = hes_mat[np.tril_indices_from(hes_mat)]
    return atnum_array, hes_tril
    # return emme, atnum_array, te_mat


def main(filename, a=False):
    fl2data(filename)
    atsyms, hes = fl2data(filename)
    if a:
        print(len(atsyms))
    else:
        print(*hes)


if __name__ == '__main__':
    # main('/home/u0133458/sftp/ko/nap/fcc/test2/bdpy01-s1-b3lyp-sg3.out')
    init()
