#!/bin/sh -e

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
sed '/^#/d; /^[[:space:]]*$/d; /^X /d; s/^+ //; s,^,debian/patches/,' debian/patches/series* | sort -u > $TMPDIR/used
find debian/patches ! -path '*/series*' -type f -name "*.diff" -o -name "*.patch" -printf "%p\n" | sort > $TMPDIR/avail
echo "Used patches"
echo "=============="
cat $TMPDIR/used
echo
echo "Unused patches"
echo "=============="
fgrep -v -f $TMPDIR/used $TMPDIR/avail || test $? = 1
echo
echo "Patches without required headers"
echo "================================"
xargs egrep -l '^(Subject|Description):' < $TMPDIR/used | xargs egrep -l '^(From|Author|Origin):' > $TMPDIR/goodheaders || test $? = 1
fgrep -v -f $TMPDIR/goodheaders $TMPDIR/used
echo
echo "Patches without Origin or Forwarded header"
echo "=========================================="
xargs egrep -L '^(Origin|Forwarded):' < $TMPDIR/used || test $? = 1
