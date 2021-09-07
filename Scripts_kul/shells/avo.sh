#!/bin/bash
if [[ $# -eq 1 ]]; then
    ~/.avogadro/openchem_build/prefix/bin/avogadro2  $1 &> /dev/null
elif [[ $# -gt 1 ]]; then
    ls $@ | xargs -i tmux neww ~/.avogadro/openchem_build/prefix/bin/avogadro2 {}
else
    ls *.log | xargs -i tmux neww ~/.avogadro/openchem_build/prefix/bin/avogadro2 {}
fi

