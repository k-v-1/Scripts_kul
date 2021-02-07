#! /bin/zsh
echo ""
if [[ `find . -maxdepth 1 -name '*.gjf-batch.log'` != "" ]]; then
for bat in ./*.gjf-batch.log; do
    leng=$(/usr/bin/wc -l $bat)
    if [[ ${leng} == *"8"* ]]; then
        rm -i $bat
    else
        echo $bat
    fi
done
fi
for job in *.gjf.job; do
    [[ -e ${job%.gjf.job}.log ]] && rm $job
done
