#!/bin/sh -e

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
awk '{if (NF >= 2) print "debian/patches/" $2}' debian/patches/series/* | sort -u > $TMPDIR/used
find debian/patches ! -path '*/series*' -type f -printf "%p\n" | sort > $TMPDIR/avail
echo "Used patches"
echo "=============="
cat $TMPDIR/used
echo
echo "Unused patches"
echo "=============="
fgrep -v -f $TMPDIR/used $TMPDIR/avail
