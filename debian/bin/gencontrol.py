#!/usr/bin/env python
import os, os.path, re, sys, textwrap, ConfigParser

class entry(dict):
    __slots__ = ('_list')

    def __init__(self):
        super(entry, self).__init__()
        self._list = []

    def __delitem__(self, key):
        super(entry, self).__delitem__(key)
        self._list.remove(key)

    def __setitem__(self, key, value):
        super(entry, self).__setitem__(key, value)
        if key.startswith('_'):
            return
        if key not in self._list:
            if 'Description' in self._list:
                self._list.insert(len(self._list)-1, key)
            else:
                self._list.append(key)

    def iterkeys(self):
        for i in self._list:
            yield i

    def iteritems(self):
        for i in self._list:
            yield (i, self[i])

class wrap(textwrap.TextWrapper):
    wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

def config():
    c = ConfigParser.ConfigParser()
    c.read("debian/arch/defines")
    return c

def config_arch(arch):
    c = config()
    c.read("debian/arch/%s/defines" % arch)
    return c

def config_subarch(arch, subarch):
    c = config_arch(arch)
    if subarch is not None:
        c.read("debian/arch/%s/%s/defines" % (arch, subarch))
    return c

def list_dirs(dir):
    ret = []
    for i in os.listdir(dir):
        if i not in ('.svn',) and os.path.isdir(os.path.join(dir, i)):
            ret.append(i)
    return ret

def list_files(dir):
    ret = []
    for i in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, i)):
            ret.append(i)
    return ret

def list_arches():
    return list_dirs("debian/arch")

def list_subarches(arch):
    ret = [None]
    ret.extend(list_dirs("debian/arch/%s" % arch))
    return ret

def list_flavours(arch, subarch):
    dir = "debian/arch/%s" % arch
    if subarch is not None:
        dir += "/%s" % subarch
    tmp = list_files(dir)
    ret = []
    for i in tmp:
        if i[:7] == 'config.':
            ret.append(i[7:])
    return ret

def read_changelog():
    r = re.compile(r"""
^
(
    (?P<header>
        (?P<header_source>\w[-+0-9a-z.]+)\ \((?P<header_version>[^\(\)\ \t]+)\)((\s+[-0-9a-zA-Z]+)+)\;
    )
)
""", re.VERBOSE)
    f = file("debian/changelog")
    entries = []
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
            e['Source'] = match.group('header_source')
            e['Version'] = match.group('header_version')
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
    match = re.match("^((\d+\.\d+)\..+?)-([^-]+)$", version)
    return (match.group(0), match.group(1), match.group(2), match.group(3))

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
        if i in (('Depends', 'Provides', 'Suggests')):
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
    entry = process_package(in_entry, vars)
    for i in (('Depends', 'Provides', 'Suggests')):
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
        entry[i] = ', '.join(value)
    if vars.has_key('desc'):
        entry['Description'] += "\n.\n" + vars['desc']
    return entry

def process_real_tree(in_entry, changelog, vars):
    entry = process_package(in_entry, vars)
    tmp = changelog[0]['Source']
    versions = []
    for i in changelog:
        if i['Source'] != tmp:
            break
        versions.insert(0, i['Version'])
    for i in (('Depends', 'Provides')):
        value = []
        tmp = entry.get(i, None)
        if tmp:
            tmp = tmp.split(',')
            for t in tmp:
                value.append(t.strip())
        if i == 'Depends':
            tmp = []
            for v in versions:
                v = parse_version(v)
                tmp.append("linux-source-%s (= %s)" % (v[1], v[0]))
            value.append(' | '.join(tmp))
        elif i == 'Provides':
            for v in versions:
                v = parse_version(v)
                value.append("linux-tree-%s" % v[0])
        entry[i] = ', '.join(value)
    return entry

def substitute(s, vars):
    def subst(match):
        return vars[match.group(1)]
    return re.sub(r'@([^@]+)@', subst, s)

def vars_changelog(vars, changelog):
    version = parse_version(changelog[0]['Version'])
    vars['srcver'] = version[0]
    vars['version'] = version[1]
    vars['major'] = version[2]
    return vars

def write_control(list):
    write_rfc822(file("debian/control", 'w'), list)

def write_makefile(list):
    f = file("debian/Makefile.inc", 'w')
    for i in list:
        f.write("%s\n" % i[0])
        if i[1] is not None:
            list = i[1]
            if isinstance(list, basestring):
                list = list.split('\n')
            for j in list:
                f.write("\t%s\n" % j)

def write_rfc822(f, list):
    for i in list:
        for j in i.iteritems():
            f.write("%s:" % j[0])
            for k in j[1].split('\n'):
              f.write(" %s\n" % k)
        f.write('\n')

if __name__ == '__main__':
    changelog = read_changelog()

    vars = {}
    vars = vars_changelog(vars, changelog)

    source_version = vars['srcver']

    vars.update(config().defaults())

    arches = {}
    subarches_architecture = {}
    for arch in list_arches():
        t1 = {}
        for subarch in list_subarches(arch):
            t2 = {}
            for flavour in list_flavours(arch, subarch):
                t2[flavour] = True
            t1[subarch] = t2
            t3 = subarches_architecture.get(subarch, {})
            t3[arch] = True
            subarches_architecture[subarch] = t3
        arches[arch] = t1

    packages = []
    makefile = []

    source = read_template("source")
    packages.append(process_package(source[0], vars))

    main = read_template("main")
    packages.extend(process_packages(main, vars))

    tree = read_template("tree")
    packages.append(process_real_tree(tree[0], changelog, vars))

    headers_main = read_template("headers.main")
    a = subarches_architecture[None].keys()
    a.sort()
    b = vars.copy()
    b['arch'] = ' '.join(a)
    packages.append(process_package(headers_main[0], b))

    headers = read_template("headers")
    headers_latest = read_template("headers.latest")
    image = read_template("image")
    image_latest = read_template("image.latest")

    i1 = arches.keys()
    i1.sort()
    for arch in i1:
        arch_vars = vars.copy()
        arch_vars['arch'] = arch
        arch_vars.update(config_arch(arch).defaults())

        i2 = arches[arch].keys()
        i2.sort()
        for subarch in i2:
            subarch_config = config_subarch(arch, subarch)
            subarch_vars = arch_vars.copy()
            subarch_vars.update(subarch_config.defaults())

            if subarch is not None:
                subarch_text = subarch
                subarch_vars['subarch'] = '%s-' % subarch
            else:
                subarch_text = 'none'
                subarch_vars['subarch'] = ''

            for i in ('binary', 'build', 'unpack'):
                makefile.append(("%s-%s:: %s-%s-%s" % (i, arch, i, arch, subarch_text), None))

            i3 = arches[arch][subarch].keys()
            i3.sort()
            for flavour in i3:
                flavour_vars = subarch_vars.copy()
                flavour_vars['flavour'] = flavour
                try:
                    flavour_vars.update(dict(subarch_config.items(flavour)))
                except ConfigParser.NoSectionError: pass
                if not flavour_vars.has_key('class'):
                    flavour_vars['class'] = '%s-class' % flavour
                if not flavour_vars.has_key('longclass'):
                    flavour_vars['longclass'] = flavour_vars['class']

                dummy_packages = []
                dummy_packages.extend(process_packages(image_latest, flavour_vars))
                packages.append(process_real_image(image[0], flavour_vars))
                dummy_packages.append(process_package(headers_latest[0], flavour_vars))
                packages.append(process_package(headers[0], flavour_vars))
                packages.extend(dummy_packages)

                for i in ('binary', 'build', 'unpack'):
                    makefile.append(("%s-%s-%s:: %s-%s-%s-%s" % (i, arch, subarch_text, i, arch, subarch_text, flavour), None))
                makefile.append(("binary-%s-%s-%s:" % (arch, subarch_text, flavour), ("$(MAKE) -f debian/Makefile binary-dummy PACKAGES_ARG='%s'" % ' '.join(["-p%s" % i['Package'] for i in dummy_packages]),)))

    extra = read_template("extra")
    packages.extend(process_packages(extra, vars))
    extra_pn = {}
    for i in extra:
        a = i['Architecture']
        pn = extra_pn.get(a, [])
        pn.append(i)
        extra_pn[a] = pn
    archs = extra_pn.keys()
    archs.sort()
    for arch in archs:
        arch_vars = vars.copy()
        arch_vars.update(config_arch(arch).defaults())

        cmds = []
        for i in extra_pn[arch]:
            makeflags = ""
            if i.has_key('X-Version-Overwrite-Epoch'):
                    makeflags = "GENCONTROL_ARGS='-v1:%s'" % source_version
            cmds.append("$(MAKE) -f debian/Makefile binary-dummy PACKAGES_ARG='-p%s' %s" % (i['Package'], makeflags))
        makefile.append(("binary-%s:: binary-%s-extra" % (arch, arch), None))
        makefile.append(("binary-%s-extra:" % arch, cmds))

    write_control(packages)
    write_makefile(makefile)


