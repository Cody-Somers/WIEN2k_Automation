#!/bin/bash

: > "foldernames_updated.txt"

while IFS="" read -r p || [ -n "$p" ]
do
  # So we grep to see if it matches in our hash table. We are grepping:
  # echo of the filename, echo of the hash of the contents
  # Remove the hash trailing features, then hash the combination of name and contents
  # If it is not found, then we put the folderpath from foldername.txt into foldernames_updated.txt
  grep -qF "$( (echo -n "$(basename "$p")" ; echo -n "$(md5sum "$p")") | cut -f 1 -d " " | tr -d "\n" | md5sum | cut -f 1 -d " " | tr -d "\n" )" "hash_table.txt" || { echo "$p" >> "foldernames_updated.txt"; }
done < foldernames.txt