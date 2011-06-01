#!/usr/bin/env python

import sys
sys.path.append("debian/lib/python")

from debian_linux.debian import *
from debian_linux.gencontrol import PackagesList, Makefile, MakeFlags
from debian_linux.utils import *

class gencontrol(object):
    makefile_targets = ('binary-arch', 'build')

    def __init__(self, underlay = None):
        self.templates = Templates(['debian/templates'])
        self.process_changelog()

    def __call__(self):
        packages = PackagesList()
        makefile = Makefile()

        self.do_source(packages)
        self.do_main(packages, makefile)

        self.write_control(packages.itervalues())
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

    def process_relation(self, key, e, in_e, vars):
        import copy
        dep = copy.deepcopy(in_e[key])
        for groups in dep:
            for item in groups:
                item.name = self.substitute(item.name, vars)
        e[key] = dep

    def process_description(self, e, in_e, vars):
        in_desc = in_e['Description']
        desc = in_desc.__class__()
        desc.short = self.substitute(in_desc.short, vars)
        for i in in_desc.long:
            desc.append(self.substitute(i, vars))
        e['Description'] = desc

    def process_package(self, in_entry, vars):
        e = Package()
        for key, value in in_entry.iteritems():
            if isinstance(value, PackageRelation):
                self.process_relation(key, e, in_entry, vars)
            elif key == 'Description':
                self.process_description(e, in_entry, vars)
            elif key[:2] == 'X-':
                pass
            else:
                e[key] = self.substitute(value, vars)
        return e

    def process_packages(self, in_entries, vars):
        entries = []
        for i in in_entries:
            entries.append(self.process_package(i, vars))
        return entries

    def substitute(self, s, vars):
        if isinstance(s, (list, tuple)):
            for i in xrange(len(s)):
                s[i] = self.substitute(s[i], vars)
            return s
        def subst(match):
            return vars[match.group(1)]
        return re.sub(r'@([a-z_]+)@', subst, s)

    def write_control(self, list):
        self.write_rfc822(file("debian/control", 'w'), list)

    def write_makefile(self, makefile):
        f = file("debian/rules.gen", 'w')
        makefile.write(f)
        f.close()

    def write_rfc822(self, f, list):
        for entry in list:
            for key, value in entry.iteritems():
                f.write("%s: %s\n" % (key, value))
            f.write('\n')

if __name__ == '__main__':
    gencontrol()()
