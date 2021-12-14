if [[ $# -le 1 ]]; then
    conda activate avogadro; avogadro $1 &> /dev/null; conda deactivate
elif [[ $# -gt 1 ]]; then
    ls $@ | xargs -i tmux neww 'source ~/anaconda3/etc/profile.d/conda.sh; conda activate avogadro; avogadro {}'
else
    ls *.log | xargs -i tmux neww conda activate avogadro; avogadro {} &> /dev/null
fi
:<<END
#!/bin/bash
if [[ $# -eq 1 ]]; then
    ~/.avogadro/openchem_build/prefix/bin/avogadro2  $1 &> /dev/null
elif [[ $# -gt 1 ]]; then
    ls $@ | xargs -i tmux neww ~/.avogadro/openchem_build/prefix/bin/avogadro2 {}
else
    ls *.log | xargs -i tmux neww ~/.avogadro/openchem_build/prefix/bin/avogadro2 {}
fi
END
