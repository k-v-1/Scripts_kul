#!/bin/bash
short=False
flst=()
tailnum=99
[[ $# -eq 0 ]] && echo "cnv.sh {{logfile(s)}} [-s]" && exit 0
while [[ "x$1" != "x" ]]; do
    case "$1" in
        -s | --short )      short=True
                            shift;;
        -r | --ratio )      ratio=True
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
        grep -FA6 "Converged?" $fl | sed -E '/^.*Predicted.*$/d; s/point so far[.]/x x Lowest/' |awk '{print $3,$4,$5}' | tr '\n' ' ' | sed 's/Threshold Converged?/\n/g; s/x x//g; s/[0-9]*//g; s/NO/NO /g'|tail -n $tailnum
    else
    if [[ "$ratio" == "True" ]]; then
        grep -FA6 "Converged?" $fl | sed -E '/^.*Predicted.*$/d; s/point so far[.]/x x Lowest/' |awk '{print $3,$4,$5}' | tr '\n' ' ' | sed 's/Threshold Converged?/\n/g; s/x x//g'| awk '{printf "%.1f %s %.1f %s %.1f %s %.1f %s %s\n", $1/$2,$3,$4/$5,$6,$7/$8,$9,$10/$11,$12,$13}'|tail -n $tailnum|column -t
    else
        grep -FA6 "Converged?" $fl | sed -E '/^.*Predicted.*$/d; s/point so far[.]/x x Lowest/' |awk '{print $3,$4,$5}' | tr '\n' ' ' | sed 's/Threshold Converged?/\n/g; s/x x//g'|tail -n $tailnum
    fi
    fi
done
echo
