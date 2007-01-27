#!/usr/bin/env python2.4
import sys
sys.path.append("debian/lib/python")
import warnings
from debian_linux.debian import *
from debian_linux.utils import *

class packages_list(sorted_dict):
    def append(self, package):
        self[package['Package']] = package

    def extend(self, packages):
        for package in packages:
            self[package['Package']] = package

class gencontrol(object):
    makefile_targets = ('binary-arch', 'build')

    def __init__(self, underlay = None):
        self.changelog = read_changelog()
        self.templates = templates()
        self.version, self.changelog_vars = self.process_changelog({})

    def __call__(self):
        packages = packages_list()
        makefile = []

        self.do_source(packages)
        self.do_main(packages, makefile)

        self.write_control(packages.itervalues())
        self.write_makefile(makefile)

    def do_source(self, packages):
        source = self.templates["control.source"]
        packages['source'] = self.process_package(source[0], self.changelog_vars)

    def do_main(self, packages, makefile):
        makeflags = {
            'VERSION': self.version['linux']['version'],
            'SOURCE_UPSTREAM': self.version['upstream'],
            'SOURCEVERSION': self.version['linux']['source'],
            'UPSTREAMVERSION': self.version['linux']['upstream'],
        }

        vars = self.changelog_vars.copy()

        self.do_main_setup(vars, makeflags)
        self.do_main_packages(packages)
        self.do_main_makefile(makefile, makeflags)

    def do_main_setup(self, vars, makeflags):
        pass

    def do_main_makefile(self, makefile, makeflags):
        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        for i in self.makefile_targets:
            makefile.append(("%s:" % i, ("$(MAKE) -f debian/rules.real %s %s" % (i, makeflags_string))))

    def do_main_packages(self, packages):
        vars = self.changelog_vars

        main = self.templates["control.main"]
        packages.extend(self.process_packages(main, vars))

    def process_changelog(self, in_vars):
        ret = [None, None]
        ret[0] = version = self.changelog[0]['Version']
        vars = in_vars.copy()
        vars['upstreamversion'] = version['linux']['upstream']
        vars['version'] = version['linux']['version']
        vars['source_upstream'] = version['upstream']
        vars['major'] = version['linux']['major']
        ret[1] = vars
        return ret

    def process_relation(self, key, e, in_e, vars):
        in_dep = in_e[key]
        dep = package_relation_list()
        for in_groups in in_dep:
            groups = package_relation_group()
            for in_item in in_groups:
                item = package_relation()
                item.name = self.substitute(in_item.name, vars)
                if in_item.version is not None:
                    item.version = self.substitute(in_item.version, vars)
                item.arches = in_item.arches
                groups.append(item)
            dep.append(groups)
        e[key] = dep

    def process_description(self, e, in_e, vars):
        in_desc = in_e['Description']
        desc = in_desc.__class__()
        desc.short = self.substitute(in_desc.short, vars)
        for i in in_desc.long:
            desc.long.append(self.substitute(i, vars))
        e['Description'] = desc

    def process_package(self, in_entry, vars):
        e = package()
        for key, value in in_entry.iteritems():
            if isinstance(value, package_relation_list):
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

    def write_makefile(self, out_list):
        out = file("debian/rules.gen", 'w')
        for item in out_list:
            if isinstance(item, (list, tuple)):
                out.write("%s\n" % item[0])
                cmd_list = item[1]
                if isinstance(cmd_list, basestring):
                    cmd_list = cmd_list.split('\n')
                for j in cmd_list:
                    out.write("\t%s\n" % j)
            else:
                out.write("%s\n" % item)

    def write_rfc822(self, f, list):
        for entry in list:
            for key, value in entry.iteritems():
                f.write("%s: %s\n" % (key, value))
            f.write('\n')


if __name__ == '__main__':
    gencontrol()()
