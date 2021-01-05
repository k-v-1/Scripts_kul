from argparse import ArgumentParser
from os import getcwd


def init():
    parser = ArgumentParser()
    parser.add_argument("dirname", help="Give name of directory with Gaussian output files")
    # todo add options for: split name; add csv + optional name; fc/es/gs force; file or dir; ...
    args = parser.parse_args()
    if args.dirname[0] in ('/', '~'):
        dirname = args.dirname
    else:
        dirname = getcwd() + '/' + args.dirname
    if dirname[-1] != '/':
        dirname = dirname + '/'
    main(dirname)
