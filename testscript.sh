#!/bin/bash

max_chars=0
for file in *.error*; do
  echo "$file"
  [ -f "$file" ] || continue
  char_count=$(wc -m < "$file")
  echo "$char_count"
  if [ "$char_count" -gt "$max_chars" ]; then
        max_chars="$char_count"
  fi
done

  if [ "$max_chars" -gt 5 ]; then
    # Run lapw here
    touch "HadToRerun.txt"
  fi