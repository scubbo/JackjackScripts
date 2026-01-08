#!/bin/bash

# This script replaces `gi`, which 99% of the time is a typo for `git` (and the remaining 1% is a typo for `vi`)
#
# If the first argument is a file, and there are no other arguments, guess that it was meant to be vi - otherwise,
# and if the first letter of the first argument is `t`, correct `gi t<whatever>` to `git <whatever>`

if [ -f "$1" ] && [ $# -eq 1 ]; then
  vi "$1";
  exit $?; # Exit with the same exit code as vi
fi

first="$1"
args=( "$@" );
echo $args
if [ ${first:0:1} == "t" ]; then
  echo "Correcting your git typo..."
  git ${first:1:${#first}} ${args[@]:1};
  exit $?;
fi

echo "Sorry, I can't figure out what you want"

