#!/bin/bash
short=False
flst=()
tailnum=99
[[ $# -eq 0 ]] && echo "cnv.sh {{logfile(s)}} [-s]" && exit 0
while [[ "x$1" != "x" ]]; do
    case "$1" in
        -s | --short )      short=True
                            shift;;
        *.log )             flst+="$1 "
                            shift;;
        [0-9]|[0-9][0-9]|[0-9][0-9][0-9] )           tailnum=$1
                            shift;;
        * )                 echo "$1 not valid"
                            shift;;
    esac
done
[[ "${flst[@]}" == "" ]] && echo "No valid logfiles" && exit 1


for fl in $flst; do
echo
echo "$fl"
    if [[ "$short" == "True" ]]; then
        grep -FA4 "Converged?" $fl | awk '{print $3,$4,$5}' | tr '\n' ' ' | sed 's/Threshold Converged?/\n/g; s/[0-9]*//g; s/NO/NO /g'|tail -n $tailnum; else
        grep -FA4 "Converged?" $fl | awk '{print $3,$4,$5}' | tr '\n' ' ' | sed 's/Threshold Converged?/\n/g'|tail -n $tailnum
    fi
echo
done
