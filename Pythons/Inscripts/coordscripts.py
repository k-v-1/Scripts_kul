import subprocess
import numpy as np
import os
import argparse
import json

atnum2sym = {1: 'H',
             2: 'He',
             3: 'Li',
             4: 'Be',
             5: 'B',
             6: 'C',
             7: 'N',
             8: 'O',
             9: 'F',
             10: 'Ne',
             11: 'Na',
             12: 'Mg',
             13: 'Al',
             14: 'Si',
             15: 'P',
             16: 'S',
             17: 'Cl',
             18: 'Ar',
             19: 'K',
             20: 'Ca',
             21: 'Sc',
             22: 'Ti',
             23: 'V',
             24: 'Cr',
             25: 'Mn',
             26: 'Fe',
             27: 'Co',
             28: 'Ni',
             29: 'Cu',
             30: 'Zn',
             31: 'Ga',
             32: 'Ge',
             33: 'As',
             34: 'Se',
             35: 'Br',
             36: 'Kr',
             37: 'Rb',
             38: 'Sr',
             39: 'Y',
             40: 'Zr',
             41: 'Nb',
             42: 'Mo',
             43: 'Tc',
             44: 'Ru',
             45: 'Rh',
             46: 'Pd',
             47: 'Ag',
             48: 'Cd',
             49: 'In',
             50: 'Sn',
             51: 'Sb',
             52: 'Te',
             53: 'I',
             54: 'Xe',
             55: 'Cs',
             56: 'Ba',
             57: 'La'}
sym2atnum = {v: k for k, v in atnum2sym.items()}


def init():
    man = '''Additional information:
    l2g file --> from gaussian xx.log, makes xx.gaus file with gaussian coordinates
    l2x file --> from gaussian xx.log, makes xx.xyz file
    l2d file -b BASINFO --> from gaussian xx.log, makes xx.dal inputfile
                            possibility to extract bs from log ##might not aways work in dalton##
    x2d file -b BASINFO --> from xx.xyz, makes xx.dal inputfile
    -b '{"bas1":atnum1, "bas2":atnum2, ...}' if not specified: '{"6-31g*":18, "aug-cc-pVDZ":57}'
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=man)
    parser.add_argument("i2j", type=str, help="choose conversion: l2g; l2x; l2d; x2d")
    parser.add_argument("filename", help="add filename")
    parser.add_argument("-b", "--basinfo", help="add optional basisset information for [l,x]2d")
    args = parser.parse_args()
    if args.filename[0] in ('/', '~'):
        filename = args.filename
    else:
        filename = os.getcwd() + '/' + args.filename
    if args.i2j == 'l2g':
        log2gaus(filename)
    elif args.i2j == 'l2x':
        log2xyz(filename)
    elif args.i2j == 'l2d':
        if args.basinfo:
            log2dal(filename, **json.loads(args.basinfo))
        else:
            log2dal(filename)
    elif args.i2j == 'x2d':
        if args.basinfo:
            xyz2dal(filename, **json.loads(args.basinfo))
        else:
            xyz2dal(filename)
    else:
        print('error')


def get_nats(filename):
    script = """
            cat %s | grep "%s" | head -n %d
            """ % (filename, 'NAtoms=', 1)
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    t = [i.decode('utf8').split() for i in p.stdout.readlines()]
    return int(t[0][1])  # returns number of atoms


def getgbas(filename):
    script = """
                grep "Standard basis:" %s | head -n1
                """ % filename
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    t = [i.decode('utf8').split() for i in p.stdout.readlines()]
    return t[0][2]  # returns basis set


def grepcoord(filename):
    nats = get_nats(filename)
    script = """
                grep -A%d "%s" %s | tail -n%d
                """ % (nats + 5, 'Standard orientation', filename, nats + 6)
    p = subprocess.Popen(script, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    t = [[i.decode('utf8').split() for i in p.stdout.readlines()]]
    return t[0]


# makes xyz from log; replaces .log with .xyz
def log2xyz(file):
    outmap = os.path.dirname(file) + '/'
    infile = file.split('/')[-1]
    outfile = infile.replace('.log', '.xyz')
    with open(outmap + outfile, "w") as wr:
        gn = grepcoord(file)[5:-1]
        fn = np.array([tuple(x) for x in gn],
                      dtype=[('c1', int), ('c2', int), ('c3', int), ('c4', float), ('c5', float), ('c6', float)])
        fn = (np.sort(fn, axis=0, order='c2'))[::-1]
        for i in range(len(fn)):
            f1 = '%.10f' % fn[i][3]
            f2 = '%.10f' % fn[i][4]
            f3 = '%.10f' % fn[i][5]
            s1 = atnum2sym[fn[i][1]]
            s2 = ' ' * (8 - len(s1)) + str(' ' if '-' not in f1 else '')
            s3 = ' ' * 5 + str(' ' if '-' not in f2 else '')
            s4 = ' ' * 5 + str(' ' if '-' not in f3 else '')
            wr.write(s1 + s2 + f1 + s3 + f2 + s4 + f3 + '\n')
    return outmap + outfile


# makes gjfcoords from log; replaces .log with .gaus
def log2gaus(file):
    outmap = os.path.dirname(file) + '/'
    infile = file.split('/')[-1]
    outfile = infile.replace('.log', '.gaus')
    with open(outmap + outfile, "w") as wr:
        gn = grepcoord(file)
        for i in range(5, len(gn) - 1):
            symb = atnum2sym[int(gn[i][1])]
            wr.write(symb + (4 - len(symb)) * ' '
                     + (14 - len(gn[i][3])) * ' ' + gn[i][3]
                     + (14 - len(gn[i][4])) * ' ' + gn[i][4]
                     + (14 - len(gn[i][5])) * ' ' + gn[i][5] + '\n')
        wr.write('\n')


# makes dalton input from xyz; replaces .xyz with .dal
# possible to add basissets for ranges of atoms by bs=atnum_max
def xyz2dal(file, **basinfo):
    def getbas(**kwargs):
        bset = [kw for kw in kwargs]
        nset = [kw for kw in kwargs.values()]
        print(bset, nset)
        if len(bset) == 0:
            print("no bs given, using standard basdic: 6-31g*=18, aug-cc-pVDZ=57")
            bset = ['6-31G*', 'aug-cc-pVDZ']
            nset = [18, 57]
        if bset[0] == 'basexcl':
            bset = [nset[0]]
            nset = [57]
        elif nset[-1] < 57:
            print('Use aug-cc-pVDZ for %d to 57' % (nset[-1] + 1))
            bset.append('aug-cc-pVDZ')
            nset.append(57)
        return bset, nset

    basnf = getbas(**basinfo)
    basdic = {}
    startval = 1
    for i in range(len(basnf[0])):
        basdic.update({j: basnf[0][i] for j in range(startval, basnf[1][i] + 1)})
        startval = basnf[1][i] + 1

    outmap = os.path.dirname(file) + '/'
    infile = file.split('/')[-1]
    outfile = infile.replace('.xyz', '.dal')
    filetemp = outmap + "temporaryyy.temp"
    with open(filetemp, "wt") as ftemp:
        with open(file, "rt") as gin:
            element = ['False']
            k = 0  # runs over all elements
            j = 0  # runs over all atoms each element
            lsum = []
            for line in gin:
                try:
                    if line.split()[0] != element[-1]:
                        if element != 'False':
                            lsum.append(j)
                        k = k + 1
                        j = 0
                        element.append(line.split()[0])
                    ftemp.write(line)
                    j = j + 1
                except IndexError:
                    continue
            lsum.append(j)
            lsum.append(k)
            print(lsum)
            print(element)

    with open(filetemp, "rt") as ftemp:
        with open(outmap + outfile, "wt") as fout:
            fout.write('ATOMBASIS\n title1\n title2\n')
            fout.write('Atomtypes=%d  NoSymmetry Angstrom\n' % lsum[-1])
            for kvar in range(1, lsum[-1] + 1):
                atnum = sym2atnum[element[kvar]]
                fout.write('Charge=%d Atoms=%d Basis=%s\n' % (atnum, lsum[kvar], basdic[atnum]))
                jvar = 1
                while jvar <= lsum[kvar]:
                    for line in ftemp:
                        fout.write(line)
                        jvar = jvar + 1
                        if jvar > lsum[kvar]:
                            break
    os.remove(filetemp)


def log2dal(file, **basinfo):
    fl2 = log2xyz(file)
    if basinfo:
        xyz2dal(fl2, **basinfo)
    else:
        while True:
            yn = input("Use basisset information from logfile? [y/n] ")
            if yn in ['y', 'n']:
                if yn == 'y':
                    basisset_log = getgbas(file)
                    xyz2dal(fl2, basexcl=basisset_log)
                if yn == 'n':
                    xyz2dal(fl2, **basinfo)
                break
            else:
                continue
    os.remove(fl2)


if __name__ == '__main__':
    init()


# from collections import namedtuple
# def creatingsym2atnum():
#     Element = namedtuple('element', 'symbol atomic_number atomic_mass group')
#     pre_dic = {
#         'Hydrogen': Element('H', 1, 1, 'Non Metals'),
#         'Helium': Element('He', 2, 4, 'Noble Gases'),
#         'Lithium': Element('Li', 3, 7, 'Alkali Metals'),
#         'Berylium': Element('Be', 4, 9, 'Alkaline Earth Metals'),
#         'Boron': Element('B', 5, 11, 'Non Metals'),
#         'Carbon': Element('C', 6, 12, 'Non Metals'),
#         'Nitrogen': Element('N', 7, 14, 'Non Metals'),
#         'Oxygen': Element('O', 8, 16, 'Non Metals'),
#         'Fluorine': Element('F', 9, 19, 'Halogens'),
#         'Neon': Element('Ne', 10, 20, 'Noble Gasses'),
#         'Sodium': Element('Na', 11, 23, 'Alkali Metals'),
#         'Magnesium': Element('Mg', 12, 24, 'Alkaline Earth Metal'),
#         'Aluminium': Element('Al', 13, 27, 'Other Metals'),
#         'Silicon': Element('Si', 14, 28, 'Non Metals'),
#         'Phosphorus': Element('P', 15, 31, 'Non Metals'),
#         'Sulphur': Element('S', 16, 32, 'Non Metals'),
#         'Chlorine': Element('Cl', 17, 35.5, 'Halogens'),
#         'Argon': Element('Ar', 18, 40, 'Noble Gasses'),
#         'Potassium': Element('K', 19, 39, 'Alkali Metals'),
#         'Calcium': Element('Ca', 20, 40, 'Alkaline Earth Metals'),
#         'Scandium': Element('Sc', 21, 45, 'Transition Metals'),
#         'Titanium': Element('Ti', 22, 48, 'Transition Metals'),
#         'Vanadium': Element('V', 23, 51, 'Transition Metals'),
#         'Chromium': Element('Cr', 24, 52, 'Transition Metals'),
#         'Manganese': Element('Mn', 25, 55, 'Transition Metals'),
#         'Iron': Element('Fe', 26, 56, 'Transition Metals'),
#         'Cobalt': Element('Co', 27, 59, 'Transition Metals'),
#         'Nickel': Element('Ni', 28, 59, 'Transition Metals'),
#         'Copper': Element('Cu', 29, 63.5, 'Transition Metals'),
#         'Zinc': Element('Zn', 30, 65, 'Transition Metals'),
#         'Gallium': Element('Ga', 31, 70, 'Other Metals'),
#         'Germanium': Element('Ge', 32, 73, 'Other Metals'),
#         'Arsenic': Element('As', 33, 75, 'Non Metals'),
#         'Selenium': Element('Se', 34, 79, 'Non Metals'),
#         'Bromine': Element('Br', 35, 80, 'Halogens'),
#         'Krypton': Element('Kr', 36, 84, 'Noble Gasses'),
#         'Rubidium': Element('Rb', 37, 85, 'Alkali Metals'),
#         'Strontium': Element('Sr', 38, 88, 'Alkaline Earth Metals'),
#         'Yttrium': Element('Y', 39, 89, 'Transition Metals'),
#         'Zirconium': Element('Zr', 40, 91, 'Transition Metals'),
#         'Niobium': Element('Nb', 41, 93, 'Transition Metals'),
#         'Molybdenum': Element('Mo', 42, 96, 'Transition Metals'),
#         'Technetium': Element('Tc', 43, 98, 'Transition Metals'),
#         'Ruthenium': Element('Ru', 44, 101, 'Transition Metals'),
#         'Rhodium': Element('Rh', 45, 103, 'Transition Metals'),
#         'Palladium': Element('Pd', 46, 106, 'Transition Metals'),
#         'Silver': Element('Ag', 47, 108, 'Transition Metals'),
#         'Cadmium': Element('Cd', 48, 112, 'Transition Metals'),
#         'Indium': Element('In', 49, 115, 'Other Metals'),
#         'Tin': Element('Sn', 50, 119, 'Other Metals'),
#         'Antimony': Element('Sb', 51, 122, 'Other Metals'),
#         'Tellurium': Element('Te', 52, 128, 'Non Metals'),
#         'Iodine': Element('I', 53, 127, 'Halogens'),
#         'Xenon': Element('Xe', 54, 131, 'Noble Gasses'),
#         'Caesium': Element('Cs', 55, 133, 'Alkali Metals'),
#         'Barium': Element('Ba', 56, 137, 'Alkaline Earth Metals'),
#         'Lanthanum': Element('La', 57, 139, 'Rare Earth Metals')}
#     for i in pre_dic:
#         print(getattr(pre_dic[i], 'atomic_number'), ': \'%s\',' % getattr(pre_dic[i], 'symbol'))
