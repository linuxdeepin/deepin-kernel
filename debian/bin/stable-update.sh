#!/bin/bash -eu

if [ $# -ne 2 ]; then
    echo >&2 "Usage: $0 REPO VERSION"
    echo >&2 "REPO is the git repository to generate a changelog from"
    echo >&2 "VERSION is the stable version (without leading v)"
    exit 2
fi

# Get base version, i.e. the Linus stable release that a version is based on
base_version() {
    local ver
    ver="${1%-rc*}"
    case "$ver" in
	2.6.*.* | [3-9].*.* | ??.*.*)
	    ver="${ver%.*}"
	    ;;
    esac
    echo "$ver"
}

add_update() {
    local base update
    base="$(base_version "$1")"
    update="${1#$base.}"
    if [ "$update" = "$1" ]; then
	update=0
    fi
    update="$((update + $2))"
    if [ $update = 0 ]; then
	echo "$base"
    else
	echo "$base.$update"
    fi
}

# Get next stable update version
next_update() {
    add_update "$1" 1
}

export GIT_DIR="$1/.git"

new_ver="$2"
cur_pkg_ver="$(dpkg-parsechangelog | sed -n 's/^Version: //p')"
cur_ver="${cur_pkg_ver%-*}"

if [ "$(base_version "$new_ver")" != "$(base_version "$cur_ver")" ]; then
    echo >&2 "$new_ver is not on the same stable series as $cur_ver"
    exit 2
fi

case "$cur_pkg_ver" in
    *~exp*)
	new_pkg_ver="$new_ver-1~exp1"
	;;
    *)
	new_pkg_ver="$new_ver-1"
	;;
esac

# dch insists on word-wrapping everything, so just add the URLs initially
dch -v "$new_pkg_ver" --preserve --multimaint-merge -D UNRELEASED \
    --release-heuristic=changelog "$(
    echo "New upstream stable update: "
    while [ "v$cur_ver" != "v$new_ver" ]; do
        cur_ver="$(next_update "$cur_ver")"
        echo "https://www.kernel.org/pub/linux/kernel/v3.x/ChangeLog-$cur_ver"
    done)"

# Then insert the shortlogs with sed
while [ "v$cur_ver" != "v$new_ver" ]; do
    next_ver="$(next_update "$cur_ver")"
    sed -i '/ChangeLog-'"${next_ver//./\\.}"'/a\
'"$(git log --reverse --pretty='    - %s\' "v$cur_ver..v$next_ver^")"'
' debian/changelog
    cur_ver="$next_ver"
done
