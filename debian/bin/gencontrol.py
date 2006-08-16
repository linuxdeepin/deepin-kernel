#!/usr/bin/env python2.4
import os, os.path, re, sys, textwrap, ConfigParser
sys.path.append("debian/lib/python")
import debian_linux.gencontrol
from debian_linux.debian import *

class gencontrol(debian_linux.gencontrol.gencontrol):
    def __init__(self):
        super(gencontrol, self).__init__()
        self.changelog = read_changelog()
        self.process_changelog()

    def do_main_setup(self, vars, makeflags):
        vars.update(self.config['image',])
        makeflags['REVISIONS'] = ' '.join([i['Version']['debian'] for i in self.changelog[::-1]])

    def do_main_packages(self, packages):
        vars = self.vars

        main = self.templates["control.main"]
        packages.extend(self.process_packages(main, vars))

        tree = self.templates["control.tree"]
        packages.append(self.process_real_tree(tree[0], vars))

        packages.extend(self.process_packages(self.templates["control.support"], vars))

    def do_arch_setup(self, vars, makeflags, arch):
        vars.update(self.config.get(('image', arch), {}))

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        headers_arch = self.templates["control.headers.arch"]
        packages_headers_arch = self.process_packages(headers_arch, vars)
        
        extra['headers_arch_depends'] = packages_headers_arch[-1]['Depends'] = package_relation_list()

        for package in packages_headers_arch:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-arch %s" % makeflags_string))
        cmds_source = []
        cmds_source.append(("$(MAKE) -f debian/rules.real source-arch %s" % makeflags_string,))
        makefile.append(("binary-arch-%s-real:" % arch, cmds_binary_arch))
        makefile.append(("build-%s-real:" % arch))
        makefile.append(("setup-%s-real:" % arch))
        makefile.append(("source-%s-real:" % arch, cmds_source))

    def do_subarch_setup(self, vars, makeflags, arch, subarch):
        vars.update(self.config.get(('image', arch, subarch), {}))
        vars['localversion_headers'] = vars['localversion']
        for i in (
            ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'),
            ('localversion_headers', 'LOCALVERSION_HEADERS'),
        ):
            if vars.has_key(i[0]):
                makeflags[i[1]] = vars[i[0]]

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
        cmds_source = []
        cmds_source.append(("$(MAKE) -f debian/rules.real source-subarch %s" % makeflags_string,))
        makefile.append(("binary-arch-%s-%s-real:" % (arch, subarch), cmds_binary_arch))
        makefile.append("build-%s-%s-real:" % (arch, subarch))
        makefile.append(("setup-%s-%s-real:" % (arch, subarch)))
        makefile.append(("source-%s-%s-real:" % (arch, subarch), cmds_source))

    def do_flavour_setup(self, vars, makeflags, arch, subarch, flavour):
        vars.update(self.config.get(('image', arch, subarch, flavour), {}))
        for i in (
            ('compiler', 'COMPILER'),
            ('image-postproc', 'IMAGE_POSTPROC'),
            ('initramfs', 'INITRAMFS',),
            ('kernel-arch', 'KERNEL_ARCH'),
            ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'),
            ('kpkg-arch', 'KPKG_ARCH'),
            ('kpkg-subarch', 'KPKG_SUBARCH'),
            ('localversion', 'LOCALVERSION'),
            ('type', 'TYPE'),
        ):
            if vars.has_key(i[0]):
                makeflags[i[1]] = vars[i[0]]

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        image_type_modulesextra = self.templates["control.image.type-modulesextra"]
        image_type_modulesinline = self.templates["control.image.type-modulesinline"]
        image_type_standalone = self.templates["control.image.type-standalone"]
        headers = self.templates["control.headers"]

        config_entry_relations = self.config.merge('relations', arch, subarch, flavour)

        image_depends = package_relation_list()
        if vars.get('initramfs', True):
            generators = vars['initramfs-generators']
            config_entry_commands_initramfs = self.config.merge('commands-image-initramfs-generators', arch, subarch, flavour)
            commands = [config_entry_commands_initramfs[i] for i in generators if config_entry_commands_initramfs.has_key(i)]
            makeflags['INITRD_CMD'] = ' '.join(commands)
            l = package_relation_group()
            l.extend(generators + ['initramfs-fallback'])
            image_depends.append(l)

        packages_own = []

        if vars['type'] == 'plain-s390-tape':
            image = image_type_standalone
        elif vars['type'] == 'plain-xen':
            image = image_type_modulesextra
        else:
            image = image_type_modulesinline

        packages_own.append(self.process_real_image(image[0], {'depends': image_depends}, config_entry_relations, vars))
        packages_own.extend(self.process_packages(image[1:], vars))

        if image in (image_type_modulesextra, image_type_modulesinline):
            makeflags['MODULES'] = True
            packages_own.append(self.process_package(headers[0], vars))
            extra['headers_arch_depends'].append('%s (= ${Source-Version})' % packages_own[-1]['Package'])

        for package in packages_own:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-flavour %s" % makeflags_string,))
        cmds_build = []
        cmds_build.append(("$(MAKE) -f debian/rules.real build %s" % makeflags_string,))
        cmds_setup = []
        cmds_setup.append(("$(MAKE) -f debian/rules.real setup-flavour %s" % makeflags_string,))
        makefile.append(("binary-arch-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_binary_arch))
        makefile.append(("build-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_build))
        makefile.append(("setup-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_setup))
        makefile.append(("source-%s-%s-%s-real:" % (arch, subarch, flavour)))

    def process_changelog(self):
        version = self.changelog[0]['Version']
        self.process_version(version)
        if version['modifier'] is not None:
            self.abiname = self.vars['abiname'] = ''
        else:
            self.abiname = self.vars['abiname'] = '-%s' % self.config['abi',]['abiname']

    def process_real_image(self, in_entry, relations, config, vars):
        entry = self.process_package(in_entry, vars)
        if vars.has_key('desc'):
            entry['Description'].long[1:1] = [vars['desc']]
        for field in 'Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts':
            value = entry.get(field, package_relation_list())
            t = vars.get(field.lower(), [])
            value.extend(t)
            t = relations.get(field.lower(), [])
            value.extend(t)
            value.config(config)
            if value:
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
