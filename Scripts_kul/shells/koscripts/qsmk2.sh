#!/bin/zsh
## qsmk2.sh
# gives available g-nodes, based on qsm and qst
if [ -n "$ZSH_VERSION" ]; then
vstat=($(ssh ko 'qstat -u koen'| tail -n+6))
vnode="gx"
nnode=3
nodelist=()
until [[ $vnode == "" ]]; do
vnode=${vstat[$nnode]}
nnode=$(($nnode+11))
if [[ ! " ${nodelist[*]} " == *" $vnode "* ]]; then
  nodelist+=($vnode)
fi
done
# nodelist=("${nodelist[@]:1}")
vnum=$((10 - ${#nodelist[@]}))
vartot=($(ssh ko 'qsum -u' | grep -A $vnum 'free' | tail -n $vnum))
# get the first elements with a g?
freelist=()
for i in {1..30}; do  # Check if node starts with g, not a member of g1..4 and use max of 5 nodes.
    [[ ${vartot[$i]} == "g"* ]] && [[ ${vartot[$i]} != "g"[1-4] ]] && [[ ${#freelist[@]} -lt $((5 - ${#nodelist[@]})) ]] && freelist+=(${vartot[$i]})
done

echo "Used: ${nodelist[*]}"
echo "Free: ${freelist[*]}"


# NOT Updated!  
elif [ -n "$BASH_VERSION" ]; then
vstat=($(qstat -u koen| tail -n+6))
vnode="gx"
nnode=2
nodelist=()
until [[ $vnode == "" ]]; do
vnode=${vstat[$nnode]}
nnode=$(($nnode+11))
if [[ ! " ${nodelist[*]} " == *" $vnode "* ]]; then
  nodelist+=($vnode)
fi
done

nodelist=("${nodelist[@]:1}")
vnum=$((5 - ${#nodelist[@]}))
vartot=($(qsum -u | grep -A $vnum 'free' | tail -n $vnum))

echo "Used: ${nodelist[*]}"
echo "Free: ${vartot[0]} ${vartot[3]} ${vartot[6]} ${vartot[9]} ${vartot[12]}"
fi
