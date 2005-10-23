import os, os.path, re, sys, textwrap, ConfigParser

class schema_item_boolean(object):
    def __call__(self, i):
        i = i.strip().lower()
        if i in ("true", "1"):
            return True
        if i in ("false", "0"):
            return False
        raise Error

class schema_item_list(object):
    def __call__(self, i):
        return re.split("\s+", i.strip())

class config(dict):
    schema = {
        'arches': schema_item_list,
        'available': schema_item_boolean,
        'flavours': schema_item_list,
        'subarches': schema_item_list,
    }

    config_name = "defines"

    def __init__(self, overlay_dir = None):
        self._overlay_dir = overlay_dir
        self._read_base()

    def __getitem__(self, key):
        if isinstance(key, basestring):
            return super(config, self).__getitem__(key)
        if isinstance(key, tuple):
            ret = {}
            ret.update(super(config, self).__getitem__('base'))
            if len(key) >= 1:
                # XXX: workaround
                del ret['abiname']
                del ret['arches']
                ret.update(super(config, self).__getitem__(key[0]))
            if len(key) >= 2:
                del ret['subarches']
                ret.update(super(config, self).__getitem__('-'.join(key[0:2])))
            if len(key) >= 3:
                del ret['flavours']
                ret.update(super(config, self).__getitem__('-'.join(key[0:3])))
            return ret
        raise NotImplemented

    def _get_files(self, name):
        ret = []
        if self._overlay_dir is not None:
            ret.append(os.path.join(self._overlay_dir, name))
        ret.append(name)
        return ret

    def _read_arch(self, arch, base):
        files = self._get_files("debian/arch/%s/%s" % (arch, self.config_name))
        c = config_parser(self.schema)
        c.read(files)
        t = c.items_convert('base')
        base.update(t)
        self[arch] = t
        subarches = t.get('subarches', [])
        for subarch in subarches:
            try:
                t2 = c.items_convert(subarch)
                avail = t2.get('available', True)
            except ConfigParser.NoSectionError:
                t2 = {}
                avail = True
            if avail:
                self._read_subarch(arch, subarch, t2)
            else:
                self['-'.join((arch, subarch))] = t2
        flavours = t.get('flavours', None)
        if flavours:
            for flavour in flavours:
                self._read_flavour(arch, 'none', flavour, c)
                self['-'.join((arch, 'none'))] = {}
            subarches.insert(0, 'none')
        t['subarches'] = subarches

    def _read_base(self):
        files = self._get_files("debian/arch/%s" % self.config_name)
        c = config_parser(self.schema)
        c.read(files)
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

    def _read_subarch(self, arch, subarch, base):
        files = self._get_files("debian/arch/%s/%s/%s" % (arch, subarch, self.config_name))
        c = config_parser(self.schema)
        c.read(files)
        t = c.items_convert('base')
        base.update(t)
        self['-'.join((arch, subarch))] = t
        flavours = t.get('flavours', None)
        for flavour in flavours:
            self._read_flavour(arch, subarch, flavour, c)

class config_parser(object, ConfigParser.ConfigParser):
    def __init__(self, schema):
        ConfigParser.ConfigParser.__init__(self)
        self.schema = schema

    def items_convert(self, section):
        items = self.items(section)
        ret = {}
        for key, value in items:
            try:
                convert = self.schema[key]()
                value = convert(value)
            except KeyError: pass
            ret[key] = value
        return ret

class _sorted_dict(dict):
    __slots__ = ('_list')

    def __init__(self):
        super(_sorted_dict, self).__init__()
        self._list = []

    def __delitem__(self, key):
        super(_sorted_dict, self).__delitem__(key)
        self._list.remove(key)

    def iterkeys(self):
        for i in iter(self._list):
            yield i

    def iteritems(self):
        for i in iter(self._list):
            yield (i, self[i])

    def itervalues(self):
        for i in iter(self._list):
            yield self[i]

class sorted_dict(_sorted_dict):
    __slots__ = ()

    def __setitem__(self, key, value):
        super(sorted_dict, self).__setitem__(key, value)
        if key not in self._list:
            self._list.append(key)

class entry(_sorted_dict):
    __slots__ = ()

    def __setitem__(self, key, value):
        super(entry, self).__setitem__(key, value)
        if key not in self._list:
            if 'Description' in self._list:
                self._list.insert(len(self._list)-1, key)
            else:
                self._list.append(key)

class wrap(textwrap.TextWrapper):
    wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

