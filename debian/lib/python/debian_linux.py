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

