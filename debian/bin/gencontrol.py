#!/usr/bin/env python

import os, sys
sys.path.append("debian/lib/python")

from debian_linux.config import ConfigCoreHierarchy
from debian_linux.debian import *
from debian_linux.gencontrol import Gencontrol as Base
from debian_linux.utils import Templates

class Gencontrol(Base):
    def __init__(self, config_dirs = ["debian/config"], template_dirs = ["debian/templates"]):
        super(Gencontrol, self).__init__(ConfigCoreHierarchy(config_dirs), Templates(template_dirs), VersionLinux)
        self.process_changelog()
        self.config_dirs = config_dirs

    def do_main_setup(self, vars, makeflags, extra):
        super(Gencontrol, self).do_main_setup(vars, makeflags, extra)
        makeflags.update({
            'MAJOR': self.version.linux_major,
            'VERSION': self.version.linux_version,
            'UPSTREAMVERSION': self.version.linux_upstream,
            'ABINAME': self.abiname,
            'SOURCEVERSION': self.version.complete,
        })

    def do_main_packages(self, packages, vars, makeflags, extra):
        packages.extend(self.process_packages(self.templates["control.main"], self.vars))

    def do_arch_setup(self, vars, makeflags, arch, extra):
        config_base = self.config.merge('base', arch)

        data = vars.copy()
        data.update(config_base)

        for i in (
            ('kernel-arch', 'KERNEL_ARCH'),
        ):
            makeflags[i[1]] = data[i[0]]

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        headers_arch = self.templates["control.headers.arch"]
        packages_headers_arch = self.process_packages(headers_arch, vars)

        libc_dev = self.templates["control.libc-dev"]
        packages_headers_arch[0:0] = self.process_packages(libc_dev, {})
        
        extra['headers_arch_depends'] = packages_headers_arch[-1]['Depends'] = PackageRelation()

        self.merge_packages(packages, packages_headers_arch, arch)

        cmds_binary_arch = ["$(MAKE) -f debian/rules.real binary-arch-arch %s" % makeflags]
        cmds_source = ["$(MAKE) -f debian/rules.real source-arch %s" % makeflags]
        makefile.add('binary-arch_%s_real' % arch, cmds = cmds_binary_arch)
        makefile.add('source_%s_real' % arch, cmds = cmds_source)

    def do_featureset_setup(self, vars, makeflags, arch, featureset, extra):
        config_base = self.config.merge('base', arch, featureset)
        makeflags['LOCALVERSION_HEADERS'] = vars['localversion_headers'] = vars['localversion']

    def do_featureset_packages(self, packages, makefile, arch, featureset, vars, makeflags, extra):
        headers_featureset = self.templates["control.headers.featureset"]
        package_headers = self.process_package(headers_featureset[0], vars)

        self.merge_packages(packages, (package_headers,), arch)

        cmds_binary_arch = ["$(MAKE) -f debian/rules.real binary-arch-featureset %s" % makeflags]
        cmds_source = ["$(MAKE) -f debian/rules.real source-featureset %s" % makeflags]
        makefile.add('binary-arch_%s_%s_real' % (arch, featureset), cmds = cmds_binary_arch)
        makefile.add('source_%s_%s_real' % (arch, featureset), cmds = cmds_source)

    def do_flavour_setup(self, vars, makeflags, arch, featureset, flavour, extra):
        config_base = self.config.merge('base', arch, featureset, flavour)
        config_description = self.config.merge('description', arch, featureset, flavour)
        config_image = self.config.merge('image', arch, featureset, flavour)

        vars['class'] = config_description['hardware']
        vars['longclass'] = config_description.get('hardware-long') or vars['class']

        vars['localversion-image'] = vars['localversion']
        override_localversion = config_image.get('override-localversion', None)
        if override_localversion is not None:
            vars['localversion-image'] = vars['localversion_headers'] + '-' + override_localversion

        data = vars.copy()
        data.update(config_base)
        data.update(config_image)

        for i in (
            ('compiler', 'COMPILER'),
            ('kernel-arch', 'KERNEL_ARCH'),
            ('localversion', 'LOCALVERSION'),
            ('type', 'TYPE'),
        ):
            makeflags[i[1]] = data[i[0]]
        for i in (
            ('cflags', 'CFLAGS_KERNEL'),
            ('initramfs', 'INITRAMFS'),
            ('kpkg-arch', 'KPKG_ARCH'),
            ('kpkg-subarch', 'KPKG_SUBARCH'),
            ('localversion-image', 'LOCALVERSION_IMAGE'),
            ('override-host-type', 'OVERRIDE_HOST_TYPE'),
        ):
            if data.has_key(i[0]):
                makeflags[i[1]] = data[i[0]]

    def do_flavour_packages(self, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
        headers = self.templates["control.headers"]

        config_entry_base = self.config.merge('base', arch, featureset, flavour)
        config_entry_description = self.config.merge('description', arch, featureset, flavour)
        config_entry_image = self.config.merge('image', arch, featureset, flavour)
        config_entry_relations = self.config.merge('relations', arch, featureset, flavour)

        compiler = config_entry_base.get('compiler', 'gcc')
        relations_compiler = PackageRelation(config_entry_relations[compiler])
        relations_compiler_build_dep = PackageRelation(config_entry_relations[compiler])
        for group in relations_compiler_build_dep:
            for item in group:
                item.arches = [arch]
        packages['source']['Build-Depends'].extend(relations_compiler_build_dep)

        image_fields = {'Description': PackageDescription()}
        for field in 'Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts':
            image_fields[field] = PackageRelation(config_entry_image.get(field.lower(), None), override_arches=(arch,))

        if config_entry_image.get('initramfs', True):
            generators = config_entry_image['initramfs-generators']
            config_entry_commands_initramfs = self.config.merge('commands-image-initramfs-generators', arch, featureset, flavour)
            commands = [config_entry_commands_initramfs[i] for i in generators if config_entry_commands_initramfs.has_key(i)]
            makeflags['INITRD_CMD'] = ' '.join(commands)
            l_depends = PackageRelationGroup()
            for i in generators:
                i = config_entry_relations.get(i, i)
                l_depends.append(i)
                a = PackageRelationEntry(i)
                if a.operator is not None:
                    a.operator = -a.operator
                    image_fields['Conflicts'].append(PackageRelationGroup([a]))
            image_fields['Depends'].append(l_depends)

        desc_parts = self.config.get_merge('description', arch, featureset, flavour, 'parts')
        if desc_parts:
            desc = image_fields['Description']
            for part in desc_parts[::-1]:
                desc.append(config_entry_description['part-long-' + part])
                desc.append_short(config_entry_description.get('part-short-' + part, ''))

        packages_dummy = []
        packages_own = []

        if config_entry_image['type'] == 'plain-s390-tape':
            image = self.templates["control.image.type-standalone"]
            build_modules = False
        elif config_entry_image['type'] == 'plain-xen':
            image = self.templates["control.image.type-modulesextra"]
            build_modules = True
            config_entry_xen = self.config.merge('xen', arch, featureset, flavour)
            if config_entry_xen.get('dom0-support', True):
                p = self.process_packages(self.templates['control.xen-linux-system'], vars)
                l = PackageRelationGroup()
                xen_versions = []
                for xen_flavour in config_entry_xen['flavours']:
                    for version in config_entry_xen['versions']:
                        l.append("xen-hypervisor-%s-%s" % (version, xen_flavour))
                        xen_versions.append('%s-%s' % (version, xen_flavour))
                makeflags['XEN_VERSIONS'] = ' '.join(xen_versions)
                p[0]['Depends'].append(l)
                packages_dummy.extend(p)
        else:
            build_modules = True
            image = self.templates["control.image.type-%s" % config_entry_image['type']]
            #image = self.templates["control.image.type-modulesinline"]

        vars.setdefault('desc', None)

        packages_own.append(self.process_real_image(image[0], image_fields, vars))
        packages_own.extend(self.process_packages(image[1:], vars))

        if build_modules:
            makeflags['MODULES'] = True
            package_headers = self.process_package(headers[0], vars)
            package_headers['Depends'].extend(relations_compiler)
            packages_own.append(package_headers)
            extra['headers_arch_depends'].append('%s (= ${binary:Version})' % packages_own[-1]['Package'])

        self.merge_packages(packages, packages_own + packages_dummy, arch)

        if config_entry_image['type'] == 'plain-xen':
            for i in ('postinst', 'postrm', 'prerm'):
                j = self.substitute(self.templates["image.xen.%s" % i], vars)
                file("debian/%s.%s" % (packages_own[0]['Package'], i), 'w').write(j)

        def get_config(*entry_name):
            entry_real = ('image',) + entry_name
            entry = self.config.get(entry_real, None)
            if entry is None:
                return None
            return entry.get('configs', None)

        def check_config_default(fail, f):
            for d in self.config_dirs[::-1]:
                f1 = d + '/' + f
                if os.path.exists(f1):
                    return [f1]
            if fail:
                raise RuntimeError("%s unavailable" % f)
            return []

        def check_config_files(files):
            ret = []
            for f in files:
                for d in self.config_dirs[::-1]:
                    f1 = d + '/' + f
                    if os.path.exists(f1):
                        ret.append(f1)
                        break
                else:
                    raise RuntimeError("%s unavailable" % f)
            return ret

        def check_config(default, fail, *entry_name):
            configs = get_config(*entry_name)
            if configs is None:
                return check_config_default(fail, default)
            return check_config_files(configs)

        kconfig = check_config('config', True)
        kconfig.extend(check_config("%s/config" % arch, True, arch))
        kconfig.extend(check_config("%s/config.%s" % (arch, flavour), False, arch, None, flavour))
        kconfig.extend(check_config("featureset-%s/config" % featureset, False, None, featureset))
        kconfig.extend(check_config("%s/%s/config" % (arch, featureset), False, arch, featureset))
        kconfig.extend(check_config("%s/%s/config.%s" % (arch, featureset, flavour), False, arch, featureset, flavour))
        makeflags['KCONFIG'] = ' '.join(kconfig)

        cmds_binary_arch = ["$(MAKE) -f debian/rules.real binary-arch-flavour %s" % makeflags]
        if packages_dummy:
            cmds_binary_arch.append("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='%s' %s" % (' '.join(["-p%s" % i['Package'] for i in packages_dummy]), makeflags))
        cmds_build = ["$(MAKE) -f debian/rules.real build %s" % makeflags]
        cmds_setup = ["$(MAKE) -f debian/rules.real setup-flavour %s" % makeflags]
        makefile.add('binary-arch_%s_%s_%s_real' % (arch, featureset, flavour), cmds = cmds_binary_arch)
        makefile.add('build_%s_%s_%s_real' % (arch, featureset, flavour), cmds = cmds_build)
        makefile.add('setup_%s_%s_%s_real' % (arch, featureset, flavour), cmds = cmds_setup)

    def do_extra(self, packages, makefile):
        apply = self.templates['patch.apply']

        vars = {
            'revisions': 'orig base ' + ' '.join([i.revision for i in self.versions[::-1]]),
            'upstream': self.version.upstream,
            'linux_upstream': self.version.linux_upstream,
            'abiname': self.abiname,
        }

        apply = self.substitute(apply, vars)

        file('debian/bin/patch.apply', 'w').write(apply)

    def merge_packages(self, packages, new, arch):
        for new_package in new:
            name = new_package['Package']
            if name in packages:
                package = packages.get(name)
                package['Architecture'].append(arch)

                for field in 'Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts':
                    if field in new_package:
                        if field in package:
                            v = package[field]
                            v.extend(new_package[field])
                        else:
                            package[field] = new_package[field]

            else:
                new_package['Architecture'] = [arch]
                packages.append(new_package)

    def process_changelog(self):
        act_upstream = self.changelog[0].version.linux_upstream
        versions = []
        for i in self.changelog:
            if i.version.linux_upstream != act_upstream:
                break
            versions.append(i.version)
        self.versions = versions
        version = self.version = self.changelog[0].version
        if self.version.linux_modifier is not None:
            self.abiname = ''
        else:
            self.abiname = '-%s' % self.config['abi',]['abiname']
        self.vars = {
            'upstreamversion': self.version.linux_upstream,
            'version': self.version.linux_version,
            'source_upstream': self.version.upstream,
            'major': self.version.linux_major,
            'abiname': self.abiname,
        }
        self.config['version',] = {'source': self.version.complete, 'abiname': self.abiname}

        distribution = self.changelog[0].distribution
        if distribution in ('unstable', ):
            if (version.linux_revision_experimental or
                    version.linux_revision_other):
                raise RuntimeError("Can't upload to %s with a version of %s" %
                        (distribution, version))
        if distribution in ('experimental', ):
            if not version.linux_revision_experimental:
                raise RuntimeError("Can't upload to %s with a version of %s" %
                        (distribution, version))

    def process_real_image(self, entry, fields, vars):
        entry = self.process_package(entry, vars)
        for key, value in fields.iteritems():
            if key in entry:
                real = entry[key]
                real.extend(value)
            elif value:
                entry[key] = value
        return entry

    def write(self, packages, makefile):
        self.write_config()
        super(Gencontrol, self).write(packages, makefile)

    def write_config(self):
        f = file("debian/config.defines.dump", 'w')
        self.config.dump(f)
        f.close()

if __name__ == '__main__':
    Gencontrol()()
