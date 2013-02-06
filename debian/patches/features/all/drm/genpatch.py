#!/usr/bin/python

import sys
sys.path.append("debian/lib/python")

import os.path, re, subprocess

from debian_linux.debian import Changelog, VersionLinux

def main(repo, drm_version):
    changelog = Changelog(version=VersionLinux)[0]

    args = ['git', 'diff',
            'v' + changelog.version.linux_upstream_full, 'v' + drm_version,
            '--', 'drivers/char/agp', 'drivers/gpu/drm', 'include/drm']
    with open('debian/patches/features/all/drm/drm-3.4.patch', 'w') as patch:
        subprocess.check_call(args, cwd=repo, stdout=patch)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >>sys.stderr, "Usage: %s REPO DRM-VERSION" % sys.argv[0]
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
