#!/usr/bin/env python2.4
import os, os.path, re, sys, textwrap, ConfigParser
sys.path.append("debian/lib/python")
import debian_linux.gencontrol
from debian_linux.debian import *

class gencontrol(debian_linux.gencontrol.gencontrol):
    def do_main_packages(self, packages):
        vars = self.changelog_vars

        main = self.templates["control.main"]
        packages.extend(self.process_packages(main, vars))

        tree = self.templates["control.tree"]
        packages.append(self.process_real_tree(tree[0], vars))

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        headers_arch = self.templates["control.headers.arch"]
        package_headers_arch = self.process_package(headers_arch[0], vars)
        extra['headers_arch_depends'] = []

        name = package_headers_arch['Package']
        if packages.has_key(name):
            package_headers_arch = packages.get(name)
            package_headers_arch['Architecture'].append(arch)
        else:
            package_headers_arch['Architecture'] = [arch]
            packages.append(package_headers_arch)

        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_setup = []
        cmds_setup.append(("$(MAKE) -f debian/rules.real setup-arch %s" % makeflags_string,))
        makefile.append(("setup-%s-real:" % arch, cmds_setup))
        makefile.append(("build-%s-real:" % arch))

    def do_arch_packages_post(self, packages, makefile, arch, vars, makeflags, extra):
        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        # Append this here so it only occurs on the install-headers-all line
#        makeflags_string += " FLAVOURS='%s' " % ' '.join(['%s' % i for i in config_entry['flavours']])
        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real install-headers-all GENCONTROL_ARGS='\"-Vkernel:Depends=%s\"' %s" % (', '.join(extra['headers_arch_depends']), makeflags_string),))
        makefile.append(("binary-arch-%s-real:" % arch, cmds_binary_arch))

    def do_subarch_makeflags(self, makeflags, arch, subarch):
        config_entry = self.config.merge('base', arch, subarch)
        for i in ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'),:
            if config_entry.has_key(i[0]):
                makeflags[i[1]] = config_entry[i[0]]

    def do_subarch_packages(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        headers_subarch = self.templates["control.headers.subarch"]
        package_headers = self.process_package(headers_subarch[0], vars)

        name = package_headers['Package']
        if packages.has_key(name):
            package_headers = packages.get(name)
            package_headers['Architecture'].append(arch)
        else:
            package_headers['Architecture'] = [arch]
            packages.append(package_headers)

        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-subarch %s" % makeflags_string,))
        cmds_setup = []
        cmds_setup.append(("$(MAKE) -f debian/rules.real setup-subarch %s" % makeflags_string,))
        makefile.append(("binary-arch-%s-%s-real:" % (arch, subarch), cmds_binary_arch))
        makefile.append("build-%s-%s-real:" % (arch, subarch))
        makefile.append(("setup-%s-%s-real:" % (arch, subarch), cmds_setup))

    def do_flavour_makeflags(self, makeflags, arch, subarch, flavour):
        config_entry = self.config.merge('base', arch, subarch, flavour)
        makeflags['TYPE'] = 'kernel-package'
        for i in (
            ('compiler', 'COMPILER'),
            ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'),
            ('kpkg-arch', 'KPKG_ARCH'),
            ('kpkg-subarch', 'KPKG_SUBARCH'),
            ('type', 'TYPE'),
        ):
            if config_entry.has_key(i[0]):
                makeflags[i[1]] = config_entry[i[0]]

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        image = self.templates["control.image"]
        headers = self.templates["control.headers"]
        image_latest = self.templates["control.image.latest"]
        headers_latest = self.templates["control.headers.latest"]

        packages_own = []
        packages_dummy = []
        packages_own.append(self.process_real_image(image[0], vars))
        packages_own.append(self.process_package(headers[0], vars))
        packages_dummy.extend(self.process_packages(image_latest, vars))
        packages_dummy.append(self.process_package(headers_latest[0], vars))

        for package in packages_own + packages_dummy:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        extra['headers_arch_depends'].append(packages_own[1]['Package'])

        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-flavour %s" % makeflags_string,))
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='%s'" % ' '.join(["-p%s" % i['Package'] for i in packages_dummy]),))
        cmds_build = []
        cmds_build.append(("$(MAKE) -f debian/rules.real build %s" % makeflags_string,))
        cmds_setup = []
        cmds_setup.append(("$(MAKE) -f debian/rules.real setup-flavour %s" % makeflags_string,))
        makefile.append(("binary-arch-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_binary_arch))
        makefile.append(("build-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_build))
        makefile.append(("setup-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_setup))

    def process_real_image(self, in_entry, vars):
        in_entry = in_entry.copy()
        if vars.has_key('desc'):
            in_entry['Description'] += "\n.\n" + vars['desc']
        entry = self.process_package(in_entry, vars)
        for field in 'Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts':
            value = entry.get(field, package_relation_list())
            t = vars.get(field.lower(), [])
            value.extend(t)
            entry[field] = value
        return entry

    def process_real_tree(self, in_entry, vars):
        entry = self.process_package(in_entry, vars)
        tmp = self.changelog[0]['Version']['upstream']
        versions = []
        for i in self.changelog:
            if i['Version']['upstream'] != tmp:
                break
            versions.insert(0, i['Version'])
        for i in (('Depends', 'Provides')):
            value = package_relation_list()
            value.extend(entry.get(i, []))
            if i == 'Depends':
                value.append("linux-patch-debian-%(version)s (= %(source)s)" % self.changelog[0]['Version'])
                value.append(' | '.join(["linux-source-%(version)s (= %(source)s)" % v for v in versions]))
            elif i == 'Provides':
                value.extend(["linux-tree-%(source)s" % v for v in versions])
            entry[i] = value
        return entry

if __name__ == '__main__':
    gencontrol()()
