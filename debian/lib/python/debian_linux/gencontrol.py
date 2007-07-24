from config import *
from debian import *
from utils import *

class PackagesList(SortedDict):
    def append(self, package):
        self[package['Package']] = package

    def extend(self, packages):
        for package in packages:
            self[package['Package']] = package

class MakeFlags(dict):
    def __repr__(self):
        repr = super(flags, self).__repr__()
        return "%s(%s)" % (self.__class__.__name__, repr)

    def __str__(self):
        return ' '.join(["%s='%s'" % i for i in self.iteritems()])

    def copy(self):
        return self.__class__(super(MakeFlags, self).copy())

class Gencontrol(object):
    makefile_targets = ('binary-arch', 'build', 'setup', 'source')

    def __init__(self, underlay = None):
        self.config = ConfigReaderCore([underlay, "debian/config"])
        self.templates = Templates()

    def __call__(self):
        packages = PackagesList()
        makefile = [('.NOTPARALLEL:', ())]

        self.do_source(packages)
        self.do_main(packages, makefile)
        self.do_extra(packages, makefile)

        self.write_control(packages.itervalues())
        self.write_makefile(makefile)

    def do_source(self, packages):
        source = self.templates["control.source"]
        packages['source'] = self.process_package(source[0], self.vars)

    def do_main(self, packages, makefile):
        config_entry = self.config['base',]
        vars = self.vars.copy()
        vars.update(config_entry)

        makeflags = MakeFlags()
        extra = {}

        self.do_main_setup(vars, makeflags, extra)
        self.do_main_packages(packages, extra)
        self.do_main_makefile(makefile, makeflags, extra)

        for arch in iter(self.config['base',]['arches']):
            self.do_arch(packages, makefile, arch, vars.copy(), makeflags.copy(), extra)

    def do_main_setup(self, vars, makeflags, extra):
        makeflags.update({
            'MAJOR': self.version.linux_major,
            'VERSION': self.version.linux_version,
            'UPSTREAMVERSION': self.version.linux_upstream,
            'ABINAME': self.abiname,
        })

    def do_main_makefile(self, makefile, makeflags, extra):
        cmds_binary_indep = []
        cmds_binary_indep.append(("$(MAKE) -f debian/rules.real binary-indep %s" % makeflags,))
        makefile.append(("binary-indep:", cmds_binary_indep))

    def do_main_packages(self, packages, extra):
        pass

    def do_extra(self, packages, makefile):
        try:
            templates_extra = self.templates["control.extra"]
        except IOError:
            return

        packages.extend(self.process_packages(templates_extra, {}))
        extra_arches = {}
        for package in templates_extra:
            arches = package['Architecture']
            for arch in arches:
                i = extra_arches.get(arch, [])
                i.append(package)
                extra_arches[arch] = i
        archs = extra_arches.keys()
        archs.sort()
        for arch in archs:
            cmds = []
            for i in extra_arches[arch]:
                tmp = []
                if i.has_key('X-Version-Overwrite-Epoch'):
                        tmp.append("-v1:%s" % self.version['source'])
                cmds.append("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='-p%s' GENCONTROL_ARGS='%s'" % (i['Package'], ' '.join(tmp)))
            makefile.append("binary-arch-%s:: binary-arch-%s-extra" % (arch, arch))
            makefile.append(("binary-arch-%s-extra:" % arch, cmds))

    def do_arch(self, packages, makefile, arch, vars, makeflags, extra):
        config_entry = self.config['base', arch]
        vars.update(config_entry)
        vars['arch'] = arch

        if not config_entry.get('available', True):
            for i in self.makefile_targets:
                makefile.append(("%s-%s:" % (i, arch), ["@echo Architecture %s is not available!" % arch, "@exit 1"]))
            return

        makeflags['ARCH'] = arch

        vars['localversion'] = ''

        self.do_arch_setup(vars, makeflags, arch, extra)
        self.do_arch_makefile(makefile, arch, makeflags, extra)
        self.do_arch_packages(packages, makefile, arch, vars, makeflags, extra)
        self.do_arch_recurse(packages, makefile, arch, vars, makeflags, extra)

    def do_arch_setup(self, vars, makeflags, arch, extra):
        pass

    def do_arch_makefile(self, makefile, arch, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s:: %s-%s" % (i, i, arch))
            makefile.append("%s-%s:: %s-%s-real" % (i, arch, i, arch))

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s-real:" % (i, arch))

    def do_arch_recurse(self, packages, makefile, arch, vars, makeflags, extra):
        for subarch in self.config['base', arch]['subarches']:
            self.do_subarch(packages, makefile, arch, subarch, vars.copy(), makeflags.copy(), extra)

    def do_subarch(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        config_entry = self.config['base', arch, subarch]
        vars.update(config_entry)

        makeflags['SUBARCH'] = subarch
        if subarch != 'none':
            vars['localversion'] += '-' + subarch

        self.do_subarch_setup(vars, makeflags, arch, subarch, extra)
        self.do_subarch_makefile(makefile, arch, subarch, makeflags, extra)
        self.do_subarch_packages(packages, makefile, arch, subarch, vars, makeflags, extra)
        self.do_subarch_recurse(packages, makefile, arch, subarch, vars, makeflags, extra)

    def do_subarch_setup(self, vars, makeflags, arch, subarch, extra):
        pass

    def do_subarch_makefile(self, makefile, arch, subarch, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s:: %s-%s-%s" % (i, arch, i, arch, subarch))
            makefile.append("%s-%s-%s:: %s-%s-%s-real" % (i, arch, subarch, i, arch, subarch))

    def do_subarch_packages(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s-%s-real:" % (i, arch, subarch))

    def do_subarch_recurse(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        for flavour in self.config['base', arch, subarch]['flavours']:
            self.do_flavour(packages, makefile, arch, subarch, flavour, vars.copy(), makeflags.copy(), extra)

    def do_flavour(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        config_entry = self.config.merge('base', arch, subarch, flavour)
        vars.update(config_entry)

        if not vars.has_key('longclass'):
            vars['longclass'] = vars['class']

        makeflags['FLAVOUR'] = flavour
        vars['localversion'] += '-' + flavour

        self.do_flavour_setup(vars, makeflags, arch, subarch, flavour, extra)
        self.do_flavour_makefile(makefile, arch, subarch, flavour, makeflags, extra)
        self.do_flavour_packages(packages, makefile, arch, subarch, flavour, vars, makeflags, extra)

    def do_flavour_setup(self, vars, makeflags, arch, subarch, flavour, extra):
        for i in (
            ('kernel-arch', 'KERNEL_ARCH'),
            ('localversion', 'LOCALVERSION'),
        ):  
            if vars.has_key(i[0]):
                makeflags[i[1]] = vars[i[0]]

    def do_flavour_makefile(self, makefile, arch, subarch, flavour, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s-%s:: %s-%s-%s-%s" % (i, arch, subarch, i, arch, subarch, flavour))
            makefile.append("%s-%s-%s-%s:: %s-%s-%s-%s-real" % (i, arch, subarch, flavour, i, arch, subarch, flavour))

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        pass

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

    def process_version_linux(self, version, abiname):
        return {
            'upstreamversion': version.linux_upstream,
            'version': version.linux_version,
            'source_upstream': version.upstream,
            'major': version.linux_major,
            'abiname': abiname,
        }

    def substitute(self, s, vars):
        if isinstance(s, (list, tuple)):
            for i in xrange(len(s)):
                s[i] = self.substitute(s[i], vars)
            return s
        def subst(match):
            return vars[match.group(1)]
        return re.sub(r'@([-_a-z]+)@', subst, s)

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


