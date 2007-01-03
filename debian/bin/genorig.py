#!/usr/bin/env python

import sys
sys.path.append("debian/lib/python")

import os, os.path, re, shutil
from debian_linux.debian import read_changelog

class main(object):
    def __init__(self, input_tar, input_patch = None):
        self.log = sys.stdout.write

        self.input_tar = input_tar
        self.input_patch = input_patch

        changelog = read_changelog()[0]
        source = changelog['Source']
        version = changelog['Version']['linux']['source_upstream']
        self.orig = '%s-%s' % (source, version)
        self.orig_tar = '%s_%s.orig.tar.gz' % (source, version)

    def __call__(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix = 'genorig', dir = 'debian')
        try:
            self.extract()
            self.patch()
            self.generate()
            self.tar()
        finally:
            pass
            shutil.rmtree(self.dir)

    def extract(self):
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
        os.rename(os.path.join(self.dir, match.group('dir')), os.path.join(self.dir, 'temp'))

    def patch(self):
        if self.input_patch is None:
            return
        self.log("Patching source with %s\n" % self.input_patch)
        match = re.match(r'(^|.*/)(patch-\d+\.\d+\.\d+(-\S+)?(\.(?P<extension>(bz2|gz))))?$', self.input_patch)
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
        cmdline.append('| (cd %s; patch -p1 -f -s -t --no-backup-if-mismatch)' % os.path.join(self.dir, 'temp'))
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't patch source")

    def generate(self):
        self.log("Generate orig\n")
        orig = os.path.join(self.dir, self.orig)
        temp = os.path.join(self.dir, 'temp')
        os.mkdir(orig)
        os.mkdir(os.path.join(orig, 'include'))
        os.mkdir(os.path.join(orig, 'include', 'linux'))
        shutil.copyfile(os.path.join(temp, 'COPYING'), os.path.join(orig, 'COPYING'))
        for i in ('input.h', 'license.h', 'mod_devicetable.h'):
            shutil.copyfile(os.path.join(temp, 'include', 'linux', i), os.path.join(orig, 'include', 'linux', i))
        shutil.copytree(os.path.join(temp, 'scripts'), os.path.join(orig, 'scripts'))

    def tar(self):
        out = os.path.join("../orig", self.orig_tar)
        self.log("Generate tarball %s\n" % out)
        cmdline = ['tar -czf', out, '-C', self.dir, self.orig]
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't patch source")

if __name__ == '__main__':
    main(*sys.argv[1:])()
