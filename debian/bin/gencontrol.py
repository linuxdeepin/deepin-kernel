#!/usr/bin/env python
import os, os.path, re, sys, textwrap, ConfigParser
sys.path.append("debian/lib/python")
from debian_linux import *

class packages_list(sorted_dict):
    def append(self, package):
        self[package['Package']] = package

    def extend(self, packages):
        for package in packages:
            self[package['Package']] = package

def read_changelog():
    r = re.compile(r"""
^
(
(?P<header>
    (?P<header_source>
        \w[-+0-9a-z.]+
    )
    \ 
    \(
    (?P<header_version>
        [^\(\)\ \t]+
    )
    \)
    \s+
    (?P<header_distribution>
        [-0-9a-zA-Z]+
    )
    \;
)
)
""", re.VERBOSE)
    f = file("debian/changelog")
    entries = []
    act_upstream = None
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip('\n')
        match = r.match(line)
        if not match:
            continue
        if match.group('header'):
            e = entry()
            e['Distribution'] = match.group('header_distribution')
            e['Source'] = match.group('header_source')
            version = parse_version(match.group('header_version'))
            e['Version'] = version
            if act_upstream is None:
                act_upstream = version['upstream']
            elif version['upstream'] != act_upstream:
                break
            entries.append(e)
    return entries

def read_rfc822(f):
    entries = []

    while True:
        e = entry()
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip('\n')
            if not line:
                break
            if line[0] in ' \t':
                if not last:
                    raise ValueError('Continuation line seen before first header')
                e[last] += '\n' + line.lstrip()
                continue
            i = line.find(':')
            if i < 0:
                raise ValueError("Not a header, not a continuation: ``%s''" % line)
            last = line[:i]
            e[last] = line[i+1:].lstrip()
        if not e:
            break

        entries.append(e)

    return entries

def read_template(name):
    return read_rfc822(file("debian/templates/control.%s.in" % name))

def parse_version(version):
    version_re = ur"""
^
(?P<source>
    (?P<parent>
        \d+\.\d+\.\d+\+
    )?
    (?P<upstream>
        (?P<version>
            (?P<major>\d+\.\d+)
            \.
            \d+
        )
        (?:
            -
            (?P<modifier>
                .+?
            )
        )?
    )
    -
    (?P<debian>[^-]+)
)
$
"""
    match = re.match(version_re, version, re.X)
    ret = match.groupdict()
    if ret['parent'] is not None:
        ret['source_upstream'] = ret['parent'] + ret['upstream']
    else:
        ret['source_upstream'] = ret['upstream']
    return ret

def process_changelog(in_vars, config, changelog):
    ret = [None, None, None, None]
    ret[0] = version = changelog[0]['Version']
    vars = in_vars.copy()
    if version['modifier'] is not None:
        ret[1] = vars['abiname'] = version['modifier']
        ret[2] = ""
    else:
        ret[1] = vars['abiname'] = config['base']['abiname']
        ret[2] = "-%s" % vars['abiname']
    vars['version'] = version['version']
    vars['major'] = version['major']
    ret[3] = vars
    return ret

def process_depends(key, e, in_e, vars):
    in_dep = in_e[key].split(',')
    dep = []
    for d in in_dep:
        d = d.strip()
        d = substitute(d, vars)
        if d:
            dep.append(d)
    if dep:
        t = ', '.join(dep)
        e[key] = t

def process_description(e, in_e, vars):
    desc = in_e['Description']
    desc_short, desc_long = desc.split ("\n", 1)
    desc_pars = [substitute(i, vars) for i in desc_long.split ("\n.\n")]
    desc_pars_wrapped = []
    w = wrap(width = 74, fix_sentence_endings = True)
    for i in desc_pars:
        desc_pars_wrapped.append(w.fill(i))
    e['Description'] = "%s\n%s" % (substitute(desc_short, vars), '\n.\n'.join(desc_pars_wrapped))

def process_package(in_entry, vars):
    e = entry()
    for i in in_entry.iterkeys():
        if i in (('Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts')):
            process_depends(i, e, in_entry, vars)
        elif i == 'Description':
            process_description(e, in_entry, vars)
        elif i[:2] == 'X-':
            pass
        else:
            e[i] = substitute(in_entry[i], vars)
    return e

def process_packages(in_entries, vars):
    entries = []
    for i in in_entries:
        entries.append(process_package(i, vars))
    return entries

def process_real_image(in_entry, vars):
    in_entry = in_entry.copy()
    if vars.has_key('desc'):
        in_entry['Description'] += "\n.\n" + vars['desc']
    entry = process_package(in_entry, vars)
    for i in (('Depends', 'Provides', 'Suggests', 'Recommends', 'Conflicts')):
        value = []
        tmp = entry.get(i, None)
        if tmp:
            tmp = tmp.split(',')
            for t in tmp:
                value.append(t.strip())
        if i == 'Depends':
            t = vars.get('depends', None)
            if t is not None:
                value.append(t)
        elif i == 'Provides':
            t = vars.get('provides', None)
            if t is not None:
                value.append(t)
        elif i == 'Suggests':
            t = vars.get('suggests', None)
            if t is not None:
                value.append(t)
        elif i == 'Recommends':
            t = vars.get('recommends', None)
            if t is not None:
                value.append(t)
        elif i == 'Conflicts':
            t = vars.get('conflicts', None)
            if t is not None:
                value.append(t)
        entry[i] = ', '.join(value)
    return entry

def process_real_tree(in_entry, changelog, vars):
    entry = process_package(in_entry, vars)
    tmp = changelog[0]['Version']['upstream']
    versions = []
    for i in changelog:
        if i['Version']['upstream'] != tmp:
            break
        versions.insert(0, i['Version'])
    for i in (('Depends', 'Provides')):
        value = []
        tmp = entry.get(i, None)
        if tmp:
            value.extend([j.strip() for j in tmp.split(',')])
        if i == 'Depends':
            value.append("linux-patch-debian-%(version)s (= %(source)s)" % changelog[0]['Version'])
            value.append(' | '.join(["linux-source-%(version)s (= %(source)s)" % v for v in versions]))
        elif i == 'Provides':
            value.extend(["linux-tree-%(source)s" % v for v in versions])
        entry[i] = ', '.join(value)
    return entry

def substitute(s, vars):
    def subst(match):
        return vars[match.group(1)]
    return re.sub(r'@([a-z_]+)@', subst, s)

def write_control(list):
    write_rfc822(file("debian/control", 'w'), list)

def write_makefile(list):
    f = file("debian/rules.gen", 'w')
    for i in list:
        f.write("%s\n" % i[0])
        if i[1] is not None:
            list = i[1]
            if isinstance(list, basestring):
                list = list.split('\n')
            for j in list:
                f.write("\t%s\n" % j)

def write_rfc822(f, list):
    for entry in list:
        for key, value in entry.iteritems():
            f.write("%s:" % key)
            if isinstance(value, tuple):
                value = value[0].join(value[1])
            for k in value.split('\n'):
              f.write(" %s\n" % k)
        f.write('\n')

def process_real_arch(packages, makefile, config, arch, vars, makeflags):
    config_entry = config[arch,]
    vars.update(config_entry)

    if not config_entry.get('available', True):
        for i in ('binary-arch', 'build', 'setup'):
            makefile.append(("%s-%s:" % (i, arch), ["@echo Architecture %s is not available!" % arch, "@exit 1"]))
        return

    headers_arch = read_template("headers.arch")
    package_headers_arch = process_package(headers_arch[0], vars)
    package_headers_arch_depends = []

    name = package_headers_arch['Package']
    if packages.has_key(name):
        package_headers_arch = packages.get(name)
        package_headers_arch['Architecture'][1].append(arch)
    else:
        package_headers_arch['Architecture'] = (' ', [arch])
        packages.append(package_headers_arch)

    for i in (('binary-arch', 'setup',)):
        makefile.append(("%s-%s:: %s-%s-real" % (i, arch, i, arch), None))

    makeflags['ARCH'] = arch
    makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

    cmds_setup = []
    cmds_setup.append(("$(MAKE) -f debian/rules.real setup-arch %s" % makeflags_string,))
    makefile.append(("setup-%s-real:" % arch, cmds_setup))

    for subarch in config_entry['subarches']:
        process_real_subarch(packages, makefile, config, arch, subarch, vars.copy(), makeflags.copy(), package_headers_arch_depends)

    # Append this here so it only occurs on the install-headers-all line
    makeflags_string += " FLAVOURS='%s' " % ' '.join(['%s' % i for i in config_entry['flavours']])
    cmds_binary_arch = []
    cmds_binary_arch.append(("$(MAKE) -f debian/rules.real install-headers-all GENCONTROL_ARGS='\"-Vkernel:Depends=%s\"' %s" % (', '.join(package_headers_arch_depends), makeflags_string),))
    makefile.append(("binary-arch-%s-real:" % arch, cmds_binary_arch))

def process_real_flavour(packages, makefile, config, arch, subarch, flavour, vars, makeflags, package_headers_arch_depends):
    config_entry = config[arch, subarch, flavour]
    vars.update(config_entry)

    vars['flavour'] = flavour
    if not vars.has_key('class'):
        vars['class'] = '%s-class' % flavour
    if not vars.has_key('longclass'):
        vars['longclass'] = vars['class']

    image = read_template("image")
    headers = read_template("headers")
    image_latest = read_template("image.latest")
    headers_latest = read_template("headers.latest")

    packages_own = []
    packages_dummy = []
    packages_own.append(process_real_image(image[0], vars))
    packages_own.append(process_package(headers[0], vars))
    packages_dummy.extend(process_packages(image_latest, vars))
    packages_dummy.append(process_package(headers_latest[0], vars))

    for package in packages_own + packages_dummy:
        name = package['Package']
        if packages.has_key(name):
            package = packages.get(name)
            package['Architecture'][1].append(arch)
        else:
            package['Architecture'] = (' ', [arch])
            packages.append(package)

    package_headers_arch_depends.append(packages_own[1]['Package'])

    for i in ('binary-arch', 'build', 'setup'):
        makefile.append(("%s-%s-%s:: %s-%s-%s-%s" % (i, arch, subarch, i, arch, subarch, flavour), None))
        makefile.append(("%s-%s-%s-%s:: %s-%s-%s-%s-real" % (i, arch, subarch, flavour, i, arch, subarch, flavour), None))

    makeflags['FLAVOUR'] = flavour
    for i in (('compiler', 'COMPILER'), ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'), ('kpkg-subarch', 'KPKG_SUBARCH'), ('kpkg-arch', 'KPKG_ARCH')):
        if config_entry.has_key(i[0]):
            makeflags[i[1]] = config_entry[i[0]]
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

def process_real_main(packages, makefile, config, version, abiname, kpkg_abiname, changelog, vars):
    source = read_template("source")
    packages['source'] = process_package(source[0], vars)

    main = read_template("main")
    packages.extend(process_packages(main, vars))

    tree = read_template("tree")
    packages.append(process_real_tree(tree[0], changelog, vars))

    makeflags = {
        'VERSION': version['version'],
        'SOURCE_UPSTREAM': version['source_upstream'],
        'SOURCE_VERSION': version['source'],
        'UPSTREAM_VERSION': version['upstream'],
        'ABINAME': abiname,
        'KPKG_ABINAME': kpkg_abiname,
        'REVISIONS': ' '.join([i['Version']['debian'] for i in changelog[::-1]]),
    }
    makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

    cmds_binary_indep = []
    cmds_binary_indep.append(("$(MAKE) -f debian/rules.real binary-indep %s" % makeflags_string,))
    makefile.append(("binary-indep:", cmds_binary_indep))

    for arch in iter(config['base']['arches']):
        process_real_arch(packages, makefile, config, arch, vars.copy(), makeflags.copy())

    extra = read_template("extra")
    packages.extend(process_packages(extra, vars))
    extra_pn = {}
    for i in extra:
        arches = i['Architecture'].split(' ')
        for arch in arches:
            pn = extra_pn.get(arch, [])
            pn.append(i)
            extra_pn[arch] = pn
    archs = extra_pn.keys()
    archs.sort()
    for arch in archs:
        arch_vars = vars.copy()
        arch_vars.update(config[arch])

        cmds = []
        for i in extra_pn[arch]:
            tmp = []
            if i.has_key('X-Version-Overwrite-Epoch'):
                    tmp.append("-v1:%s" % version['source'])
            cmds.append("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='-p%s' GENCONTROL_ARGS='%s'" % (i['Package'], ' '.join(tmp)))
        makefile.append(("binary-arch-%s:: binary-arch-%s-extra" % (arch, arch), None))
        makefile.append(("binary-arch-%s-extra:" % arch, cmds))

def process_real_subarch(packages, makefile, config, arch, subarch, vars, makeflags, package_headers_arch_depends):
    if subarch == 'none':
        vars['subarch'] = ''
    else:
        vars['subarch'] = '%s-' % subarch
    config_entry = config[arch, subarch]
    vars.update(config_entry)

    headers_subarch = read_template("headers.subarch")

    package_headers = process_package(headers_subarch[0], vars)

    name = package_headers['Package']
    if packages.has_key(name):
        package_headers = packages.get(name)
        package_headers['Architecture'][1].append(arch)
    else:
        package_headers['Architecture'] = (' ', [arch])
        packages.append(package_headers)

    for i in ('binary-arch', 'build', 'setup'):
        makefile.append(("%s-%s:: %s-%s-%s" % (i, arch, i, arch, subarch), None))
        makefile.append(("%s-%s-%s::" % (i, arch, subarch), None))
    for i in ('binary-arch', 'setup'):
        makefile.append(("%s-%s-%s:: %s-%s-%s-real" % (i, arch, subarch, i, arch, subarch), None))

    makeflags['SUBARCH'] = subarch
    for i in ('kernel-header-dirs', 'KERNEL_HEADER_DIRS'),:
        if config_entry.has_key(i[0]):
            makeflags[i[1]] = config_entry[i[0]]
    makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

    cmds_binary_arch = []
    cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-subarch %s" % makeflags_string,))
    cmds_setup = []
    cmds_setup.append(("$(MAKE) -f debian/rules.real setup-subarch %s" % makeflags_string,))
    makefile.append(("binary-arch-%s-%s-real:" % (arch, subarch), cmds_binary_arch))
    makefile.append(("setup-%s-%s-real:" % (arch, subarch), cmds_setup))

    for flavour in config_entry['flavours']:
        process_real_flavour(packages, makefile, config, arch, subarch, flavour, vars.copy(), makeflags.copy(), package_headers_arch_depends)

def main():
    changelog = read_changelog()

    c = config()

    version, abiname, kpkg_abiname, vars = process_changelog({}, c, changelog)

    packages = packages_list()
    makefile = []

    process_real_main(packages, makefile, c, version, abiname, kpkg_abiname, changelog, vars)

    write_control(packages.itervalues())
    write_makefile(makefile)


if __name__ == '__main__':
    main()
