#!/bin/sh -e

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
sed '/^#/d; /^[[:space:]]*$/d; s/^[+X] //; s,^,debian/patches/,' debian/patches/series* | sort -u > $TMPDIR/used
find debian/patches ! -path '*/series*' -type f -name "*.diff" -o -name "*.patch" -printf "%p\n" | sort > $TMPDIR/avail
echo "Used patches"
echo "=============="
cat $TMPDIR/used
echo
echo "Unused patches"
echo "=============="
fgrep -v -f $TMPDIR/used $TMPDIR/avail
