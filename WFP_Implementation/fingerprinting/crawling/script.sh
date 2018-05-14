#!/bin/bash


for d in data/*/ ; do
  for e in $d* ; do     
     cp $e .
     B="$(cut -d'/' -f3 <<<"$e")"
     ./fetch-and-calculate.sh test100 180 $B
     wait
     rm $B
  done
done



