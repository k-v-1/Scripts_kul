#!/bin/bash
echo "name, SCF Done, totE after corr, Corr transE, emmE_clr"
for clr5 in *clr5.log; do
    bname=${clr5%clr5.log}
    clr4=${bname}clr4.log
    cte=($(grep "Corrected transition energy" $clr4 | awk '{print $5}'))
    teac=($(grep "Total energy after correction" $clr4 | awk '{print $6}'))
    scfd=($(grep "SCF Done" $clr5 | awk '{print $5}'))
    emme=($(echo "($teac - $scfd)*27.212"|bc))
    echo "$bname, $scfd, $teac, $cte, $emme"
done

