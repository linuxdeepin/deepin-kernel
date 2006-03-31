#!/bin/sh -e

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
awk '{if (NF >= 2) print $2}' debian/patches/series/* | sort -u > $TMPDIR/used
find debian/patches -maxdepth 1 -type f -printf "%f\n" | sort > $TMPDIR/avail
echo "Used patches"
echo "=============="
cat $TMPDIR/used
echo
echo "Unused patches"
echo "=============="
fgrep -v -f $TMPDIR/used $TMPDIR/avail
