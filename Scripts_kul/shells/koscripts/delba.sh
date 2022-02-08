#! /usr/bin/env zsh
echo ""
if [[ `find . -maxdepth 1 -name '*.gjf-batch.log'` != "" ]]; then
for bat in ./*.gjf-batch.log; do
    [[ `tail -n1 ${bat%gjf-batch.log}log | awk '{print $1}'` != "Normal" ]] && echo "ErRoR $bat"
    leng=$(/usr/bin/wc -l $bat)
    if [[ ${leng} == *"8"* ]] || [[ ${leng} == *"0"* ]] ; then
        rm -i $bat
    else
        echo $bat
    fi
done
fi
for job in *.gjf.job; do
    [[ -e ${job%.gjf.job}.log ]] && rm $job
done
