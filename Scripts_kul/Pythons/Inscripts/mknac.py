import argparse
import os
import re


def init():
    man = '''
    MOMAP-mirror:
        Extracts transition elements from gaussian nac-file
        Gives nacme(x) = TE*atnum/emmE(a.u.) to Stdout
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=man)
    parser.add_argument("filename", help="add filename")
    args = parser.parse_args()
    if args.filename[0] in ('/', '~'):
        filename = args.filename
    else:
        filename = os.getcwd() + '/' + args.filename

    main(filename)


def fl2data(filename):
    atnum_flag = 0
    atnum_array = []
    emm_e_flag = False
    emme = 0
    te_flag = 0
    te_mat = []
    with open(filename, "r") as fl:
        for line in fl.readlines():
            if re.search(r'Coordinates \(Angstroms\)', line):
                atnum_flag = 1
            if atnum_flag > 0:
                if atnum_flag > 3:
                    if re.search("-------------", line):
                        atnum_flag = 0
                    else:
                        atnum_array.append(line.split()[1])
                else:
                    atnum_flag += 1

            if re.search('Excitation energies and oscillator strengths', line):
                emm_e_flag = True
            if emm_e_flag:
                if re.search("This state for", line):
                    emm_e_flag = False
                elif re.search("Excited State {3}", line):
                    emme = line.split()[4]

            if re.search("-------- Electric Field --------", line):
                te_flag = 1
            if te_flag > 0:
                if te_flag > 3:
                    if re.search("-------------", line):
                        te_flag = 0
                    else:
                        te_mat.append(line.split()[3:6])
                else:
                    te_flag += 1
    # print(atnum_array)
    # print(te_mat)
    # print(emme)
    return emme, atnum_array, te_mat


def main(filename):
    emme, atnums, tes = fl2data(filename)
    e_au = float(emme)/27.212
    nacmat = [[float(tes[j][i])*int(atnums[j])/float(e_au) for i in range(3)] for j in range(len(tes))]
    nacprint = [["{:.9f}".format(elem) for elem in rw] for rw in nacmat]
    [print(*i) for i in nacprint]


if __name__ == '__main__':
    # main('/home/u0133458/Documents/Calc/nap/mmp/m-set/ct/04/m1104nac.log')
    init()
