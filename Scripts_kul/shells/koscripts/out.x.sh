#!/bin/zsh
##
# TODO switch grep to full sed
rm -f keep
keepname='keep'
if [ $# -eq 0 ]; then # if no arguments: find pathern to match outputfile
  cat $PWD/*.o?????? > $PWD/cat.o000000
  name=$PWD/cat.o000000
elif [ $# -eq 1 ]; then # if 1 arg: use this file to compress
  name=$1
elif [ $# -eq 2 ]; then # if 2 args: use second arg instead of default 'keep' name
  name=$1
  keepname=$2
fi
#echo "name = $name"
cp $name keep
grep -v "_" keep > rem; mv rem keep
grep -v "Copyright" keep > rem; mv rem keep
grep -v "Institute" keep > rem; mv rem keep
grep -v "Reserved" keep > rem; mv rem keep
sed -i '/^[[:space:]]*$/d' keep 
ls -l *.o?????? >> keep
if [ $keepname != 'keep' ]; then
  mv keep $keepname
fi
vi $keepname
