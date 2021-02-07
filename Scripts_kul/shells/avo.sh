#!/bin/bash
if [[ $# -eq 1 ]]; then
    avogadro $1 &> /dev/null
elif [[ $# -gt 1 ]]; then
    ls $@ | xargs -i tmux neww avogadro {}
else
    ls *.log | xargs -i tmux neww avogadro {}
fi

