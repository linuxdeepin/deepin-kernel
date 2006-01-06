import itertools, re, utils

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
            e = {}
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
    if match is None:
        raise ValueError
    ret = match.groupdict()
    if ret['parent'] is not None:
        ret['source_upstream'] = ret['parent'] + ret['upstream']
    else:
        ret['source_upstream'] = ret['upstream']
    return ret

class package_relation(object):
    __slots__ = "name", "version", "arches"

    _re = re.compile(r'^(\S+)(?: \(([^)]+)\))?(?: \[([^]]+)\])?$')

    def __init__(self, value = None):
        if value is not None:
            match = self._re.match(value)
            if match is None:
                raise RuntimeError, "Can't parse dependency %s" % value
            match = match.groups()
            self.name = match[0]
            self.version = match[1]
            if match[2] is not None:
                self.arches = re.split('\s+', match[2])
            else:
                self.arches = []
        else:
            self.name = None
            self.version = None
            self.arches = []

    def __str__(self):
        ret = [self.name]
        if self.version is not None:
            ret.extend([' (', self.version, ')'])
        if self.arches:
            ret.extend([' [', ' '.join(self.arches), ']'])
        return ''.join(ret)

class package_relation_list(list):
    def __init__(self, value = None):
        if isinstance(value, (list, tuple)):
            self.extend(value)
        elif value is not None:
            self.extend(value)

    def __str__(self):
        return ', '.join([str(i) for i in self])

    def _match(self, value):
        for i in self:
            if i._match(value):
                return i
        return None

    def extend(self, value):
        if isinstance(value, basestring):
            value = [package_relation_group(j.strip()) for j in re.split(',', value.strip())]
        for i in value:
            if isinstance(i, basestring):
                i = package_relation_group(i)
            j = self._match(i)
            if j:
                j._update_arches(i)
            else:
                self.append(i)

class package_relation_group(list):
    def __init__(self, value = None):
        if isinstance(value, package_relation_list):
            self.extend(value)
        elif value is not None:
            self._extend(value)

    def __str__(self):
        return ' | '.join([str(i) for i in self])

    def _extend(self, value):
        self.extend([package_relation(j.strip()) for j in re.split('\|', value.strip())])

    def _match(self, value):
        for i, j in itertools.izip(self, value):
            if i.name != j.name or i.version != j.version:
                return None
        return self

    def _update_arches(self, value):
        for i, j in itertools.izip(self, value):
            if i.arches:
                for arch in j.arches:
                    if arch not in i.arches:
                        i.arches.append(arch)

class package(dict):
    _fields = utils.sorted_dict((
        ('Package', str),
        ('Source', str),
        ('Architecture', utils.field_list),
        ('Section', str),
        ('Priority', str),
        ('Maintainer', str),
        ('Uploaders', str),
        ('Standards-Version', str),
        ('Build-Depends', package_relation_list),
        ('Build-Depends-Indep', package_relation_list),
        ('Provides', package_relation_list),
        ('Depends', package_relation_list),
        ('Recommends', package_relation_list),
        ('Suggests', package_relation_list),
        ('Replaces', package_relation_list),
        ('Conflicts', package_relation_list),
        ('Description', utils.field_string),
    ))

    def __setitem__(self, key, value):
        try:
            value = self._fields[key](value)
        except KeyError: pass
        super(package, self).__setitem__(key, value)

    def iterkeys(self):
        for i in self._fields.iterkeys():
            if self.has_key(i) and self[i]:
                yield i

    def iteritems(self):
        for i in self._fields.iterkeys():
            if self.has_key(i) and self[i]:
                yield (i, self[i])

    def itervalues(self):
        for i in self._fields.iterkeys():
            if self.has_key(i) and self[i]:
                yield self[i]

