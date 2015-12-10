#!/usr/bin/env python3

import sys
sys.path.append("debian/lib/python")

from debian_linux.debian import *
from debian_linux.gencontrol import PackagesList, Makefile, MakeFlags, Gencontrol
from debian_linux.utils import *

class gencontrol(Gencontrol):
    makefile_targets = ('binary-arch', 'binary-indep', 'build-arch', 'build-indep')

    def __init__(self, underlay = None):
        self.templates = Templates(['debian/templates'])
        self.process_changelog()

    def __call__(self):
        packages = PackagesList()
        makefile = Makefile()

        self.do_source(packages)
        self.do_main(packages, makefile)

        self.write_control(packages.values())
        self.write_makefile(makefile)

    def do_source(self, packages):
        source = self.templates["control.source"]
        packages['source'] = self.process_package(source[0], self.vars)

    def do_main(self, packages, makefile):
        vars = self.vars.copy()
        makeflags = MakeFlags()

        self.do_main_setup(vars, makeflags)
        self.do_main_packages(packages)
        self.do_main_makefile(makefile, makeflags)

    def do_main_setup(self, vars, makeflags):
        makeflags.update({
            'VERSION': self.version.linux_version,
            'VERSION_DEBIAN': self.version.complete,
            'UPSTREAMVERSION': self.version.linux_upstream,
        })

    def do_main_makefile(self, makefile, makeflags):
        for i in self.makefile_targets:
            makefile.add(i, cmds = ["$(MAKE) -f debian/rules.real %s %s" % (i, makeflags)])

    def do_main_packages(self, packages):
        main = self.templates["control.main"]
        packages.extend(self.process_packages(main, self.vars))

    def process_changelog(self):
        changelog = Changelog(version = VersionLinux)
        self.version = version = changelog[0].version
        self.vars = {
            'upstreamversion': version.linux_upstream,
            'version': version.linux_version,
            'source_upstream': version.upstream,
        }

if __name__ == '__main__':
    gencontrol()()
