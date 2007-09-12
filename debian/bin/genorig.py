#!/usr/bin/env python

import sys
sys.path.append("debian/lib/python")

import os, os.path, re, shutil
from debian_linux.debian import Changelog, VersionLinux
from debian_linux.patches import PatchSeries

class Main(object):
    def __init__(self, input_tar, input_patch = None):
        self.log = sys.stdout.write

        self.input_tar = input_tar
        self.input_patch = input_patch

        changelog = Changelog(version = VersionLinux)[0]
        source = changelog.source
        self.version = changelog.version
        self.orig = '%s-%s' % (source, changelog.version.upstream)
        self.orig_tar = '%s_%s.orig.tar.gz' % (source, changelog.version.upstream)

    def __call__(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix = 'genorig', dir = 'debian')
        try:
            self.upstream_extract()
            self.upstream_patch()
            self.debian_patch()
            self.tar()
        finally:
            shutil.rmtree(self.dir)

    def upstream_extract(self):
        self.log("Extracting tarball %s\n" % self.input_tar)
        match = re.match(r'(^|.*/)(?P<dir>linux-\d+\.\d+\.\d+(-\S+)?)\.tar(\.(?P<extension>(bz2|gz)))?$', self.input_tar)
        if not match:
            raise RuntimeError("Can't identify name of tarball")
        cmdline = ['tar -xf', self.input_tar, '-C', self.dir]
        if match.group('extension') == 'bz2':
            cmdline.append('-j')
        elif match.group('extension') == 'gz':
            cmdline.append('-z')
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't extract tarball")
        os.rename(os.path.join(self.dir, match.group('dir')), os.path.join(self.dir, self.orig))

    def upstream_patch(self):
        if self.input_patch is None:
            return
        self.log("Patching source with %s\n" % self.input_patch)
        match = re.match(r'(^|.*/)patch-\d+\.\d+\.\d+(-\S+?)?(\.(?P<extension>(bz2|gz)))?$', self.input_patch)
        if not match:
            raise RuntimeError("Can't identify name of patch")
        cmdline = []
        if match.group('extension') == 'bz2':
            cmdline.append('bzcat')
        elif match.group('extension') == 'gz':
            cmdline.append('zcat')
        else:
            cmdline.append('cat')
        cmdline.append(self.input_patch)
        cmdline.append('| (cd %s; patch -p1 -f -s -t --no-backup-if-mismatch)' % os.path.join(self.dir, self.orig))
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't patch source")

    def debian_patch(self):
        version = self.version.linux_dfsg
        if version is None:
            name = "orig-0"
        else:
            name = "orig-" + version
        self.log("Patching source with debian patch (series %s)\n" % name)
        fp = file("debian/patches/series/" + name)
        series = PatchSeries(name, "debian/patches", fp)
        series(dir = os.path.join(self.dir, self.orig))

    def tar(self):
        out = os.path.join("../orig", self.orig_tar)
        try:
            os.mkdir("../orig")
        except OSError: pass
        try:
            os.stat(out)
            raise RuntimeError("Destination already exists")
        except OSError: pass
        self.log("Generate tarball %s\n" % out)
        cmdline = ['tar -czf', out, '-C', self.dir, self.orig]
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't patch source")
        os.chmod(out, 0644)

if __name__ == '__main__':
    Main(*sys.argv[1:])()
