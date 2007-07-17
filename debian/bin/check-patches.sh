#!/bin/sh -e

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
grep -v "^#"  debian/patches/series/* | awk '{if (NF >= 2) print "debian/patches/" $2}' | sort -u > $TMPDIR/used
find debian/patches ! -path '*/series*' -type f -name "*.diff" -o -name "*.patch" -printf "%p\n" | sort > $TMPDIR/avail
echo "Used patches"
echo "=============="
cat $TMPDIR/used
echo
echo "Unused patches"
echo "=============="
fgrep -v -f $TMPDIR/used $TMPDIR/avail
