#!/bin/zsh

names=()
for chk in "$@"; do
fullname=`pwd`/$chk
names+=($(echo $fullname|sed 's#/home/u0133458/sftp/ko#/home/koen#'))
done
echo $names
ssh t1 ssh ko ssh node3 exec /bin/sh -s <<EOF
for fl in $names; do
/usr/local/chem/g16A03/formchk \$fl
done
EOF
