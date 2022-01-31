#!/bin/bash
infofunc () {
local flname=$1
`grep -q "ricc2 : all done" $flname` && local dn="all done" || local dn="Error"
local gse=($(grep "Total Energy" $flname | awk '{print $4}'))
local eses=($(grep "sym | multi | state" -A4 ricc2.out | tail -n3 | awk '{print $8}' | tr "\n" " "))
local esss=($(grep "sym | multi | state" -A4 ricc2.out | tail -n3 | awk '{print $10}' | tr "\n" " "))
local esfs=($(grep "oscillator strength (length gauge)" ricc2.out | awk '{print $6}' | tr "\n" " "))
echo "$flname $gse $dn"
echo "${eses[@]}"
echo "${esfs[@]}"
echo "${esss[@]}"
echo ""
}
pw0=`pwd`
if [[ $# -eq 0 ]]; then
    dirs=.
else
    dirs=$@
fi
for dir in ${dirs[@]}; do
    fls=($(grep -l "R I C C 2 - PROGRAM" $pw0/$dir/*))
    for fl in ${fls[@]}; do
        infofunc $fl
    done
done
