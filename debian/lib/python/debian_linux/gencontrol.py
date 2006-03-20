import warnings
from config import *
from debian import *
from utils import *

class packages_list(sorted_dict):
    def append(self, package):
        self[package['Package']] = package

    def extend(self, packages):
        for package in packages:
            self[package['Package']] = package

class gencontrol(object):
    makefile_targets = ('binary-arch', 'build', 'setup', 'source')

    def __init__(self, underlay = None):
        self.changelog = read_changelog()
        self.config = config_reader([underlay, "debian/arch"])
        self.templates = templates()
        self.version, self.abiname, self.changelog_vars = self.process_changelog({})

    def __call__(self):
        packages = packages_list()
        makefile = []

        self.do_source(packages)
        self.do_main(packages, makefile)
        self.do_extra(packages, makefile)

        self.write_control(packages.itervalues())
        self.write_makefile(makefile)

    def do_source(self, packages):
        source = self.templates["control.source"]
        packages['source'] = self.process_package(source[0], self.changelog_vars)

    def do_main(self, packages, makefile):
        makeflags = {
            'VERSION': self.version['version'],
            'SOURCE_UPSTREAM': self.version['source_upstream'],
            'SOURCEVERSION': self.version['source'],
            'UPSTREAMVERSION': self.version['upstream'],
            'ABINAME': self.abiname,
            'REVISIONS': ' '.join([i['Version']['debian'] for i in self.changelog[::-1]]),
        }

        vars = self.changelog_vars.copy()

        self.do_main_setup(vars, makeflags)
        self.do_main_packages(packages)
        self.do_main_makefile(makefile, makeflags)

        for arch in iter(self.config['base',]['arches']):
            self.do_arch(packages, makefile, arch, vars.copy(), makeflags.copy())

    def do_main_setup(self, vars, makeflags):
        pass

    def do_main_makefile(self, makefile, makeflags):
        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_indep = []
        cmds_binary_indep.append(("$(MAKE) -f debian/rules.real binary-indep %s" % makeflags_string,))
        makefile.append(("binary-indep:", cmds_binary_indep))

    def do_main_packages(self, packages):
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

    def do_arch(self, packages, makefile, arch, vars, makeflags):
        config_entry = self.config['base', arch]
        vars.update(config_entry)

        if not config_entry.get('available', True):
            for i in self.makefile_targets:
                makefile.append(("%s-%s:" % (i, arch), ["@echo Architecture %s is not available!" % arch, "@exit 1"]))
            return

        extra = {}
        makeflags['ARCH'] = arch

        vars['localversion'] = ''

        self.do_arch_setup(vars, makeflags, arch)
        self.do_arch_makefile(makefile, arch, makeflags)
        self.do_arch_packages(packages, makefile, arch, vars, makeflags, extra)

        for subarch in config_entry['subarches']:
            self.do_subarch(packages, makefile, arch, subarch, vars.copy(), makeflags.copy(), extra)

        self.do_arch_packages_post(packages, makefile, arch, vars, makeflags, extra)

    def do_arch_setup(self, vars, makeflags, arch):
        pass

    def do_arch_makefile(self, makefile, arch, makeflags):
        for i in self.makefile_targets:
            makefile.append("%s:: %s-%s" % (i, i, arch))
            makefile.append("%s-%s:: %s-%s-real" % (i, arch, i, arch))

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s-real:" % (i, arch))

    def do_arch_packages_post(self, packages, makefile, arch, vars, makeflags, extra):
        pass

    def do_subarch(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        config_entry = self.config['base', arch, subarch]
        vars.update(config_entry)

        makeflags['SUBARCH'] = subarch
        if subarch != 'none':
            vars['localversion'] += '-' + subarch

        self.do_subarch_setup(vars, makeflags, arch, subarch)
        self.do_subarch_makefile(makefile, arch, subarch, makeflags)
        self.do_subarch_packages(packages, makefile, arch, subarch, vars, makeflags, extra)

        for flavour in config_entry['flavours']:
            self.do_flavour(packages, makefile, arch, subarch, flavour, vars.copy(), makeflags.copy(), extra)

    def do_subarch_setup(self, vars, makeflags, arch, subarch):
        pass

    def do_subarch_makefile(self, makefile, arch, subarch, makeflags):
        for i in self.makefile_targets:
            makefile.append("%s-%s:: %s-%s-%s" % (i, arch, i, arch, subarch))
            makefile.append("%s-%s-%s:: %s-%s-%s-real" % (i, arch, subarch, i, arch, subarch))

    def do_subarch_packages(self, packages, makefile, arch, subarch, vars, makeflags, extra):
        for i in self.makefile_targets:
            makefile.append("%s-%s-%s-real:" % (i, arch, subarch))

    def do_flavour(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        config_entry = self.config['base', arch, subarch, flavour]
        vars.update(config_entry)

        if not vars.has_key('class'):
            warnings.warn('No class entry in config for flavour %s, subarch %s, arch %s' % (flavour, subarch, arch), DeprecationWarning)
            vars['class'] = '%s-class' % flavour
        if not vars.has_key('longclass'):
            vars['longclass'] = vars['class']

        config_base = self.config.merge('base', arch)
        config_relations = self.config.merge('relations', arch)
        compiler = config_base.get('compiler', 'gcc')
        relations_compiler = package_relation_list(config_relations[compiler])
        for group in relations_compiler:
            for item in group:
                item.arches = [arch]
        packages['source']['Build-Depends'].extend(relations_compiler)

        makeflags['FLAVOUR'] = flavour
        vars['localversion'] += '-' + flavour

        self.do_flavour_setup(vars, makeflags, arch, subarch, flavour)
        self.do_flavour_makefile(makefile, arch, subarch, flavour, makeflags)
        self.do_flavour_packages(packages, makefile, arch, subarch, flavour, vars, makeflags, extra)

    def do_flavour_setup(self, vars, makeflags, arch, subarch, flavour):
        for i in (
            ('compiler', 'COMPILER'),
            ('kernel-arch', 'KERNEL_ARCH'),
            ('localversion', 'LOCALVERSION'),
        ):  
            if vars.has_key(i[0]):
                makeflags[i[1]] = vars[i[0]]

    def do_flavour_makefile(self, makefile, arch, subarch, flavour, makeflags):
        for i in self.makefile_targets:
            makefile.append("%s-%s-%s:: %s-%s-%s-%s" % (i, arch, subarch, i, arch, subarch, flavour))
            makefile.append("%s-%s-%s-%s:: %s-%s-%s-%s-real" % (i, arch, subarch, flavour, i, arch, subarch, flavour))

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        pass

    def process_changelog(self, in_vars):
        ret = [None, None, None]
        ret[0] = version = self.changelog[0]['Version']
        vars = in_vars.copy()
        if version['modifier'] is not None:
            ret[1] = vars['abiname'] = ''
        else:
            ret[1] = vars['abiname'] = '-%s' % self.config['abiname',]['abiname']
        vars['upstreamversion'] = version['upstream']
        vars['version'] = version['version']
        vars['major'] = version['major']
        ret[2] = vars
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


