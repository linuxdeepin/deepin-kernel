from config import *
from debian import *
from utils import *

class PackagesList(SortedDict):
    def append(self, package):
        self[package['Package']] = package

    def extend(self, packages):
        for package in packages:
            self[package['Package']] = package

class Makefile(object):
    def __init__(self):
        self.rules = {}
        self.add('.NOTPARALLEL')

    def add(self, name, deps = None, cmds = None):
        if name in self.rules:
            self.rules[name].add(deps, cmds)
        else:
            self.rules[name] = self.Rule(name, deps, cmds)

    def write(self, out):
        r = self.rules.keys()
        r.sort()
        for i in r:
            self.rules[i].write(out)

    class Rule(object):
        def __init__(self, name, deps = None, cmds = None):
            self.name = name
            self.deps, self.cmds = set(), []
            self.add(deps, cmds)

        def add(self, deps = None, cmds = None):
            if deps is not None:
                self.deps.update(deps)
            if cmds is not None:
                self.cmds.append(cmds)

        def write(self, out):
            deps_string = ''
            if self.deps:
                deps = list(self.deps)
                deps.sort()
                deps_string = ' ' + ' '.join(deps)

            if self.cmds:
                if deps_string:
                    out.write('%s::%s\n' % (self.name, deps_string))
                for c in self.cmds:
                    out.write('%s::\n' % self.name)
                    for i in c:
                        out.write('\t%s\n' % i)
            else:
                out.write('%s:%s\n' % (self.name, deps_string))

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

    def __init__(self, config_dirs, template_dirs):
        self.config = ConfigReaderCore(config_dirs)
        self.templates = Templates(template_dirs)

    def __call__(self):
        packages = PackagesList()
        makefile = Makefile()

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
        makefile.add('binary-indep', cmds = ["$(MAKE) -f debian/rules.real binary-indep %s" % makeflags])

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
            makefile.add('binary-arch_%s' % arch ['binary-arch_%s_extra' % arch])
            makefile.add("binary-arch_%s_extra" % arch, cmds = cmds)

    def do_arch(self, packages, makefile, arch, vars, makeflags, extra):
        config_base = self.config['base', arch]
        vars.update(config_base)
        vars['arch'] = arch

        makeflags['ARCH'] = arch

        self.do_arch_setup(vars, makeflags, arch, extra)
        self.do_arch_makefile(makefile, arch, makeflags, extra)
        self.do_arch_packages(packages, makefile, arch, vars, makeflags, extra)
        self.do_arch_recurse(packages, makefile, arch, vars, makeflags, extra)

    def do_arch_setup(self, vars, makeflags, arch, extra):
        pass

    def do_arch_makefile(self, makefile, arch, makeflags, extra):
        for i in self.makefile_targets:
            target1 = i
            target2 = "%s_%s" % (i, arch)
            makefile.add(target1, [target2])
            makefile.add(target2, ['%s_real' % target2])
            makefile.add('%s_real' % target2)

    def do_arch_packages(self, packages, makefile, arch, vars, makeflags, extra):
        pass

    def do_arch_recurse(self, packages, makefile, arch, vars, makeflags, extra):
        for featureset in self.config['base', arch]['featuresets']:
            self.do_featureset(packages, makefile, arch, featureset, vars.copy(), makeflags.copy(), extra)

    def do_featureset(self, packages, makefile, arch, featureset, vars, makeflags, extra):
        config_base = self.config.merge('base', arch, featureset)
        vars.update(config_base)

        if not config_base.get('enabled', True):
            return

        makeflags['FEATURESET'] = featureset

        vars['localversion'] = ''
        if featureset != 'none':
            vars['localversion'] = '-' + featureset

        self.do_featureset_setup(vars, makeflags, arch, featureset, extra)
        self.do_featureset_makefile(makefile, arch, featureset, makeflags, extra)
        self.do_featureset_packages(packages, makefile, arch, featureset, vars, makeflags, extra)
        self.do_featureset_recurse(packages, makefile, arch, featureset, vars, makeflags, extra)

    def do_featureset_setup(self, vars, makeflags, arch, featureset, extra):
        pass

    def do_featureset_makefile(self, makefile, arch, featureset, makeflags, extra):
        for i in self.makefile_targets:
            target1 = "%s_%s" % (i, arch)
            target2 = "%s_%s_%s" % (i, arch, featureset)
            makefile.add(target1, [target2])
            makefile.add(target2, ['%s_real' % target2])
            makefile.add('%s_real' % target2)

    def do_featureset_packages(self, packages, makefile, arch, featureset, vars, makeflags, extra):
        pass

    def do_featureset_recurse(self, packages, makefile, arch, featureset, vars, makeflags, extra):
        for flavour in self.config['base', arch, featureset]['flavours']:
            self.do_flavour(packages, makefile, arch, featureset, flavour, vars.copy(), makeflags.copy(), extra)

    def do_flavour(self, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
        config_base = self.config.merge('base', arch, featureset, flavour)
        vars.update(config_base)

        if not vars.has_key('longclass'):
            vars['longclass'] = vars['class']

        makeflags['FLAVOUR'] = flavour
        vars['localversion'] += '-' + flavour

        self.do_flavour_setup(vars, makeflags, arch, featureset, flavour, extra)
        self.do_flavour_makefile(makefile, arch, featureset, flavour, makeflags, extra)
        self.do_flavour_packages(packages, makefile, arch, featureset, flavour, vars, makeflags, extra)

    def do_flavour_setup(self, vars, makeflags, arch, featureset, flavour, extra):
        for i in (
            ('kernel-arch', 'KERNEL_ARCH'),
            ('localversion', 'LOCALVERSION'),
        ):  
            if vars.has_key(i[0]):
                makeflags[i[1]] = vars[i[0]]

    def do_flavour_makefile(self, makefile, arch, featureset, flavour, makeflags, extra):
        for i in self.makefile_targets:
            target1 = "%s_%s_%s" % (i, arch, featureset)
            target2 = "%s_%s_%s_%s" % (i, arch, featureset, flavour)
            makefile.add(target1, [target2])
            makefile.add(target2, ['%s_real' % target2])
            makefile.add('%s_real' % target2)

    def do_flavour_packages(self, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
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

    def write_makefile(self, makefile):
        f = file("debian/rules.gen", 'w')
        makefile.write(f)
        f.close()

    def write_rfc822(self, f, list):
        for entry in list:
            for key, value in entry.iteritems():
                f.write("%s: %s\n" % (key, value))
            f.write('\n')


