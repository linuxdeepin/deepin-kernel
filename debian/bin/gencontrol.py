#!/usr/bin/env python
import os, os.path, re, sys, textwrap, ConfigParser

config_name = "defines"

class schema_item_boolean(object):
    def __call__(self, i):
        i = i.strip().lower()
        if i in ("true", "1"):
            return True
        if i in ("false", "0"):
            return False
        raise Error

class schema_item_integer(object):
    def __call__(self, i):
        return int(i)

class schema_item_list(object):
    def __call__(self, i):
        return re.split("\s+", i.strip())

class schema_item_string(object):
    def __call__(self, i):
        return str(i)

class config(dict):
    schema = {
        'abiname': schema_item_string,
        'arches': schema_item_list,
        'available': schema_item_boolean,
        'class': schema_item_string,
        'depends': schema_item_string,
        'desc': schema_item_string,
        'flavours': schema_item_list,
        'kpkg-subarch': schema_item_string,
        'longclass': schema_item_string,
        'subarches': schema_item_list,
        'suggests': schema_item_string,
    }

    def __init__(self):
        self._read_base()

    def _read_arch(self, arch, base):
        file = "debian/arch/%s/%s" % (arch, config_name)
        c = config_parser(self.schema)
        c.read(file)
        t = c.items_convert('base')
        base.update(t)
        self[arch] = t
        subarches = t.get('subarches', [])
        for subarch in subarches:
            raise RuntimeError
        flavours = t.get('flavours', None)
        if flavours:
            for flavour in flavours:
                self._read_flavour(arch, 'none', flavour, c)
            subarches.append('none')
        t['subarches'] = subarches

    def _read_base(self):
        file = "debian/arch/%s" % config_name
        c = config_parser(self.schema)
        c.read(file)
        t1 = c.items_convert('base')
        self['base'] = t1
        for arch in t1['arches']:
            try:
                t2 = c.items_convert(arch)
                avail = t2.get('available', True)
            except ConfigParser.NoSectionError:
                t2 = {}
                avail = True
            if avail:
                self._read_arch(arch, t2)
            else:
                self[arch] = t2

    def _read_flavour(self, arch, subarch, flavour, c):
        try:
            t = c.items_convert(flavour)
        except ConfigParser.NoSectionError:
            try:
                t = c.items_convert("%s-none-%s" % (arch, flavour))
            except ConfigParser.NoSectionError:
                #raise RuntimeError("Don't find config for %s-none-%s!" % (arch, flavour))
                t = {}
        self["%s-%s-%s" % (arch, subarch, flavour)] = t

class config_parser(object, ConfigParser.ConfigParser):
    def __init__(self, schema):
        ConfigParser.ConfigParser.__init__(self)
        self.schema = schema

    def items_convert(self, section):
        items = self.items(section)
        ret = {}
        for key, value in items:
            convert = self.schema[key]()
            ret[key] = convert(value)
        return ret

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
            e['Version'] = parse_version(match.group('header_version'))
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
    (
        \d+\.\d+\.\d+\+
    )?
    (?P<upstream>
        (?P<version>
            (?P<major>\d+\.\d+)
            \.
            \d+
        )
        (
            -
            .+?
        )?
    )
    -
    (?P<debian>[^-]+)
)
$
"""
    match = re.match(version_re, version, re.X)
    return match.groupdict()

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
    in_entry = in_entry.copy()
    if vars.has_key('desc'):
        in_entry['Description'] += "\n.\n" + vars['desc']
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

def vars_changelog(vars, changelog):
    version = changelog[0]['Version']
    vars['version'] = version['version']
    vars['major'] = version['major']
    return vars

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
    for i in list:
        for j in i.iteritems():
            f.write("%s:" % j[0])
            for k in j[1].split('\n'):
              f.write(" %s\n" % k)
        f.write('\n')

def main():
    changelog = read_changelog()

    vars = {}
    vars = vars_changelog(vars, changelog)

    version = changelog[0]['Version']

    c = config()

    vars.update(c['base'])

    arches = {}
    subarches_architecture = {}
    for arch in c['base']['arches']:
        if not c[arch].get('available', True):
            continue
        t1 = {}
        for subarch in c[arch].get('subarches', []):
            t2 = {}
            if subarch != 'none':
                for flavour in c["%s-%s" % (arch, subarch)].get('flavours', []):
                    t2[flavour] = True
            else:
                for flavour in c[arch].get('flavours', []):
                    t2[flavour] = True
                subarch = None
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

    makeflags = [
        "VERSION='%s'" % version['version'],
        "SOURCE_VERSION='%s'" % version['source'],
        "UPSTREAM_VERSION='%s'" % version['upstream'],
    ]
    cmds_binary_indep = []
    cmds_binary_indep.append(("$(MAKE) -f debian/rules.real binary-indep %s" % ' '.join(makeflags),))
    makefile.append(("binary-indep:", cmds_binary_indep))

    arch_list = arches.keys()
    arch_list.sort()
    for arch in arch_list:
        arch_vars = vars.copy()
        arch_vars['arch'] = arch
        arch_vars.update(c[arch])

        for i in (('setup',)):
            makefile.append(("%s-%s:: %s-%s-real" % (i, arch, i, arch), None))

        arch_makeflags = makeflags[:]
        arch_makeflags.append("ARCH='%s'" % arch)
        cmds_setup = []
        cmds_setup.append(("$(MAKE) -f debian/rules.real setup-arch %s" % ' '.join(arch_makeflags),))
        makefile.append(("setup-%s-real:" % arch, cmds_setup))

        subarch_list = arches[arch].keys()
        subarch_list.sort()
        for subarch in subarch_list:
            subarch_vars = arch_vars.copy()

            if subarch is not None:
                subarch_text = subarch
                subarch_vars['subarch'] = '%s-' % subarch
                subarch_vars.update(c['%s-%s' % (arch, subarch)])
            else:
                subarch_text = 'none'
                subarch_vars['subarch'] = ''

            for i in ('binary-arch', 'build', 'setup'):
                makefile.append(("%s-%s:: %s-%s-%s" % (i, arch, i, arch, subarch_text), None))
                makefile.append(("%s-%s-%s::" % (i, arch, subarch_text), None))
            for i in ('binary-arch', 'setup'):
                makefile.append(("%s-%s-%s:: %s-%s-%s-real" % (i, arch, subarch_text, i, arch, subarch_text), None))

            subarch_makeflags = arch_makeflags[:]
            subarch_makeflags.extend(["SUBARCH='%s'" % subarch_text, "ABINAME='%s'" % subarch_vars['abiname']])
            subarch_makeflags_clean = subarch_makeflags[:]
            if subarch_vars.has_key('kpkg-subarch'):
                subarch_makeflags.append("KPKG_SUBARCH='%s'" % subarch_vars['kpkg-subarch'])

            cmds_binary_arch = []
            cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-subarch %s" % ' '.join(subarch_makeflags),))
            cmds_setup = []
            cmds_setup.append(("$(MAKE) -f debian/rules.real setup-subarch %s" % ' '.join(subarch_makeflags),))
            makefile.append(("binary-arch-%s-%s-real:" % (arch, subarch_text), cmds_binary_arch))
            makefile.append(("setup-%s-%s-real:" % (arch, subarch_text), cmds_setup))

            flavour_list = arches[arch][subarch].keys()
            flavour_list.sort()
            for flavour in flavour_list:
                flavour_vars = subarch_vars.copy()
                flavour_vars['flavour'] = flavour

                try:
                    flavour_vars.update(c['%s-%s-%s' % (arch, subarch_text, flavour)])
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

                for i in ('binary-arch', 'build', 'setup'):
                    makefile.append(("%s-%s-%s:: %s-%s-%s-%s" % (i, arch, subarch_text, i, arch, subarch_text, flavour), None))
                    makefile.append(("%s-%s-%s-%s:: %s-%s-%s-%s-real" % (i, arch, subarch_text, flavour, i, arch, subarch_text, flavour), None))

                flavour_makeflags = subarch_makeflags_clean[:]
                flavour_makeflags.append("FLAVOUR='%s'" % flavour)
                if flavour_vars.has_key('kpkg-subarch'):
                    flavour_makeflags.append("KPKG_SUBARCH='%s'" % flavour_vars['kpkg-subarch'])
                cmds_binary_arch = []
                cmds_binary_arch.append(("$(MAKE) -f debian/rules.real binary-arch-flavour %s" % ' '.join(flavour_makeflags),))
                cmds_binary_arch.append(("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='%s'" % ' '.join(["-p%s" % i['Package'] for i in dummy_packages]),))
                cmds_build = []
                cmds_build.append(("$(MAKE) -f debian/rules.real build %s" % ' '.join(flavour_makeflags),))
                cmds_setup = []
                cmds_setup.append(("$(MAKE) -f debian/rules.real setup-flavour %s" % ' '.join(flavour_makeflags),))
                makefile.append(("binary-arch-%s-%s-%s-real:" % (arch, subarch_text, flavour), cmds_binary_arch))
                makefile.append(("build-%s-%s-%s-real:" % (arch, subarch_text, flavour), cmds_build))
                makefile.append(("setup-%s-%s-%s-real:" % (arch, subarch_text, flavour), cmds_setup))

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
        arch_vars.update(c[arch])

        cmds = []
        for i in extra_pn[arch]:
            tmp = []
            if i.has_key('X-Version-Overwrite-Epoch'):
                    tmp.append("-v1:%s" % version['source'])
            cmds.append("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='-p%s' GENCONTROL_ARGS='%s'" % (i['Package'], ' '.join(tmp)))
        makefile.append(("binary-arch-%s:: binary-arch-%s-extra" % (arch, arch), None))
        makefile.append(("binary-arch-%s-extra:" % arch, cmds))

    write_control(packages)
    write_makefile(makefile)


if __name__ == '__main__':
    main()
