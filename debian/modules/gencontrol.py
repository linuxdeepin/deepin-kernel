#!/usr/bin/env python2.4
import sys
sys.path.append(sys.path[0] + "/../lib/python")
import debian_linux.gencontrol
from debian_linux.config import *
from debian_linux.debian import *

class gencontrol(debian_linux.gencontrol.gencontrol):
    def __init__(self, config):
        super(gencontrol, self).__init__(config)
        self.process_config_version(config_parser({}, [sys.path[0] + "/../version"]))

    def do_main_packages(self, packages, extra):
        vars = self.vars

        main = self.templates["control.main"]
        packages.extend(self.process_packages(main, vars))

        packages['source']['Build-Depends'].extend(
            ['linux-support-%s%s' % (self.version['upstream'], self.abiname)]
        )
        packages['source']['Build-Depends'].extend(
            ['linux-headers-%s%s-all-%s [%s]' % (self.version['upstream'], self.abiname, arch, arch)
            for arch in self.config['base',]['arches']],
        )

    def do_flavour(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        config_entry = self.config.merge('base', arch, subarch, flavour)
        if config_entry.get('modules', True) is False:
            return

        super(gencontrol, self).do_flavour(packages, makefile, arch, subarch, flavour, vars, makeflags, extra)

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        modules = self.templates["control.modules"]
        modules = self.process_packages(modules, vars)

        for package in modules:
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

    def process_config_version(self, config):
        entry = config['version',]
        self.version = parse_version(entry['source'])
        self.abiname = entry['abiname']
        self.vars = self.process_version_linux(self.version, self.abiname)

if __name__ == '__main__':
    gencontrol(sys.path[0] + "/../arch")()
