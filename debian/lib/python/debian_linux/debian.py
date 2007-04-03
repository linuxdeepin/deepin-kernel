import itertools, os.path, re, utils

class Changelog(list):
    _rules = r"""
^
(?P<source>
    \w[-+0-9a-z.]+
)
\ 
\(
(?P<version>
    [^\(\)\ \t]+
)
\)
\s+
(?P<distribution>
    [-+0-9a-zA-Z.]+
)
\;
"""
    _re = re.compile(_rules, re.X)

    class Entry(object):
        __slot__ = 'distribution', 'source', 'version'

        def __init__(self, distribution, source, version):
            self.distribution, self.source, self.version = distribution, source, version

    def __init__(self, dir = '', version = None):
        if version is None:
            version = Version
        f = file(os.path.join(dir, "debian/changelog"))
        while True:
            line = f.readline()
            if not line:
                break
            match = self._re.match(line)
            if not match:
                continue
            try:
                v = version(match.group('version'))
            except Exception:
                if not len(self):
                    raise
                v = Version(match.group('version'))
            self.append(self.Entry(match.group('distribution'), match.group('source'), v))

class Version(object):
    _version_rules = ur"""
^
(?:
    (?P<epoch>
        \d+
    )
    :
)?
(?P<upstream>
    .+?
)   
(?:
    -
    (?P<debian>[^-]+)
)?
$
"""
    _version_re = re.compile(_version_rules, re.X)

    def __init__(self, version):
        match = self._version_re.match(version)
        if match is None:
            raise RuntimeError, "Invalid debian version"
        self.complete = version
        self.epoch = None
        if match.group("epoch") is not None:
            self.epoch = int(match.group("epoch"))
        self.upstream = match.group("upstream")
        self.debian = match.group("debian")

        if self.debian is not None:
            self.complete_noepoch = "%s-%s" % (self.upstream, self.debian)
        else:
            self.complete_noepoch = self.upstream

    def __str__(self):
        return self.complete

class VersionLinux(Version):
    _version_linux_rules = ur"""
^
(?P<version>
    (?P<major>\d+\.\d+)
    \.
    \d+
)
(?:
    ~
    (?P<modifier>
        .+?
    )
)?
(?:
    \.dfsg\.\d+
)?
-
(?:[^-]+)
$
"""
    _version_linux_re = re.compile(_version_linux_rules, re.X)

    def __init__(self, version):
        super(VersionLinux, self).__init__(version)
        match = self._version_linux_re.match(version)
        if match is None:
            raise RuntimeError, "Invalid debian linux version"
        d = match.groupdict()
        self.linux_major = d['major']
        self.linux_modifier = d['modifier']
        self.linux_version = d['version']
        if d['modifier'] is not None:
            self.linux_upstream = '-'.join((d['version'], d['modifier']))
        else:
            self.linux_upstream = d['version']
 
class package_description(object):
    __slots__ = "short", "long"

    def __init__(self, value = None):
        self.long = []
        if value is not None:
            self.short, long = value.split("\n", 1)
            self.append(long)
        else:
            self.short = None

    def __str__(self):
        ret = self.short + '\n'
        w = utils.wrap(width = 74, fix_sentence_endings = True)
        pars = []
        for i in self.long:
            pars.append('\n '.join(w.wrap(i)))
        return self.short + '\n ' + '\n .\n '.join(pars)

    def append(self, str):
        str = str.strip()
        if str:
            self.long.extend(str.split("\n.\n"))

class package_relation(object):
    __slots__ = "name", "operator", "version", "arches"

    _re = re.compile(r'^(\S+)(?: \((<<|<=|=|!=|>=|>>)\s*([^)]+)\))?(?: \[([^]]+)\])?$')

    class _operator(object):
        OP_LT = 1
        OP_LE = 2
        OP_EQ = 3
        OP_NE = 4
        OP_GE = 5
        OP_GT = 6

        operators = {
            '<<': OP_LT,
            '<=': OP_LE,
            '=':  OP_EQ,
            '!=': OP_NE,
            '>=': OP_GE,
            '>>': OP_GT,
        }
        operators_neg = {
            OP_LT: OP_GE,
            OP_LE: OP_GT,
            OP_EQ: OP_NE,
            OP_NE: OP_EQ,
            OP_GE: OP_LT,
            OP_GT: OP_LE,
        }
        operators_text = dict([(b, a) for a, b in operators.iteritems()])

        __slots__ = '_op',

        def __init__(self, value):
            self._op = self.operators[value]

        def __neg__(self):
            return self.__class__(self.operators_text[self.operators_neg[self._op]])

        def __str__(self):
            return self.operators_text[self._op]

    def __init__(self, value = None):
        if value is not None:
            self.parse(value)
        else:
            self.name = None
            self.operator = None
            self.version = None
            self.arches = []

    def __str__(self):
        ret = [self.name]
        if self.operator is not None and self.version is not None:
            ret.extend([' (', str(self.operator), ' ', self.version, ')'])
        if self.arches:
            ret.extend([' [', ' '.join(self.arches), ']'])
        return ''.join(ret)

    def config(self, entry):
        if self.version is not None or self.arches:
            return
        value = entry.get(self.name, None)
        if value is None:
            return
        self.parse(value)

    def parse(self, value):
        match = self._re.match(value)
        if match is None:
            raise RuntimeError, "Can't parse dependency %s" % value
        match = match.groups()
        self.name = match[0]
        if match[1] is not None:
            self.operator = self._operator(match[1])
        else:
            self.operator = None
        self.version = match[2]
        if match[3] is not None:
            self.arches = re.split('\s+', match[3])
        else:
            self.arches = []

class package_relation_list(list):
    def __init__(self, value = None):
        if value is not None:
            self.extend(value)

    def __str__(self):
        return ', '.join([str(i) for i in self])

    def _match(self, value):
        for i in self:
            if i._match(value):
                return i
        return None

    def append(self, value):
        if isinstance(value, basestring):
            value = package_relation_group(value)
        elif not isinstance(value, package_relation_group):
            raise ValueError, "got %s" % type(value)
        j = self._match(value)
        if j:
            j._update_arches(value)
        else:
            super(package_relation_list, self).append(value)

    def config(self, entry):
        for i in self:
            i.config(entry)

    def extend(self, value):
        if isinstance(value, basestring):
            value = [j.strip() for j in re.split(',', value.strip())]
        elif not isinstance(value, (list, tuple)):
            raise ValueError, "got %s" % type(value)
        for i in value:
            self.append(i)

class package_relation_group(list):
    def __init__(self, value = None):
        if value is not None:
            self.extend(value)

    def __str__(self):
        return ' | '.join([str(i) for i in self])

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

    def append(self, value):
        if isinstance(value, basestring):
            value = package_relation(value)
        elif not isinstance(value, package_relation):
            raise ValueError
        super(package_relation_group, self).append(value)

    def config(self, entry):
        for i in self:
            i.config(entry)

    def extend(self, value):
        if isinstance(value, basestring):
            value = [j.strip() for j in re.split('\|', value.strip())]
        elif not isinstance(value, (list, tuple)):
            raise ValueError
        for i in value:
            self.append(i)

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
        ('Pre-Depends', package_relation_list),
        ('Depends', package_relation_list),
        ('Recommends', package_relation_list),
        ('Suggests', package_relation_list),
        ('Replaces', package_relation_list),
        ('Conflicts', package_relation_list),
        ('Description', package_description),
    ))

    def __setitem__(self, key, value):
        try:
            cls = self._fields[key]
            if not isinstance(value, cls):
                value = cls(value)
        except KeyError: pass
        super(package, self).__setitem__(key, value)

    def iterkeys(self):
        keys = set(self.keys())
        for i in self._fields.iterkeys():
            if self.has_key(i):
                keys.remove(i)
                yield i
        for i in keys:
            yield i

    def iteritems(self):
        for i in self.iterkeys():
            yield (i, self[i])

    def itervalues(self):
        for i in self.iterkeys():
            yield self[i]

