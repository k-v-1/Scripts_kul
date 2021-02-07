#!/bin/zsh
## qsmk.sh
# gives first $1 available g-nodes

if ! [ -n "$ZSH_VERSION" ]; then
echo "only for ZSH"
fi

vnum=7
[[ $# -gt 1 ]] && echo "only give number of nodes" && exit 1
[[ $# -eq 1 ]] && vnum=$1
vartot=($(ssh ko 'qsum -u' | grep -A $vnum 'free' | tail -n $vnum))
freelist=()
for i in {1..$((vnum * 3))}; do  # Check if node starts with g, not a member of g1..4 and use max of 5 nodes.
    [[ ${vartot[$i]} == "g"* ]] && [[ ${#freelist[@]} -lt $vnum ]] && freelist+=(${vartot[$i]})
done

echo ${freelist[*]}

