# Scripts_kul
Some useful and less useful scripts for working with dirac and quantum chemistry in/output files
Probably no one will ever use this :p 

## Pythonscripts
usefull scripts for analysis (Definitely check the help [-h] for these!):
* anafcc.py : analyses FCClasses output + able to plot abs, emi, ic and nr spectra!
* anagaus16_v2 : analyses Gaussian16 output

usefull scripts for input preparation:
* coordscripts.py : can convert xyz, fchk, Dalton, and Gaussian input coordinates into eachother
* gaus2orca.py : can convert Gaussian .fchk to Orca .hess file (Can then be used in FCC calcs!)

(extra)
* littlescripts.py : defines some functions used for other scripts (so needed to let the other scripts work)


## Shellscripts
See also my other repo for useful submitscripts in dirac.
* cs : combination of cd, ls and mkdir
* aliases, vimrc, zshrc, tmux.conf : you might find something usefull here
* koscripts/cnv.sh : to see how far a G16 *.log optimization has converged (check script for -s and -r flags)
