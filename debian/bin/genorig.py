#!/usr/bin/env python

import sys
sys.path.append("debian/lib/python")

import os, os.path, re, shutil
from debian_linux.debian import read_changelog

class main(object):
    def __init__(self, input_tar, input_patch):
        self.log = sys.stdout.write

        self.input_tar = input_tar
        self.input_patch = input_patch

        changelog = read_changelog()[0]
        source = changelog['Source']
        version = changelog['Version']['upstream']
        self.orig = '%s-%s' % (source, version)
        self.orig_tar = '%s_%s.orig.tar.gz' % (source, version)

    def __call__(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix = 'genorig', dir = 'debian')
        try:
            self.extract()
            self.patch()
            self.tar()
        finally:
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
        os.rename(os.path.join(self.dir, match.group('dir')), os.path.join(self.dir, self.orig))

    def patch(self):
        self.log("Patching with debian patch source-%s\n" % self.input_patch)
        cmdline = 'cd %s; python2.4 ../../templates/patch.apply.in --overwrite-home=../../patches --orig=%s' % (os.path.join(self.dir, self.orig), self.input_patch)
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', cmdline]):
            raise RuntimeError("Can't extract tarball")

    def tar(self):
        out = os.path.join("../orig", self.orig_tar)
        self.log("Generate tarball %s\n" % out)
        cmdline = ['tar -czf', out, '-C', self.dir, self.orig]
        if os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)]):
            raise RuntimeError("Can't patch source")
        os.chmod(out, 0644)

if __name__ == '__main__':
    main(*sys.argv[1:])()
