import os, os.path, re, sys, textwrap

__all__ = [
    'ConfigParser',
    'ConfigReaderCore',
]

_marker = object()

class SchemaItemBoolean(object):
    def __call__(self, i):
        i = i.strip().lower()
        if i in ("true", "1"):
            return True
        if i in ("false", "0"):
            return False
        raise Error

class SchemaItemList(object):
    def __init__(self, type = "\s+"):
        self.type = type

    def __call__(self, i):
        i = i.strip()
        if not i:
            return []
        return [j.strip() for j in re.split(self.type, i)]

class ConfigReaderCore(dict):
    config_name = "defines"

    schemas = {
        'base': {
            'arches': SchemaItemList(),
            'available': SchemaItemBoolean(),
            'flavours': SchemaItemList(),
            'modules': SchemaItemBoolean(),
            'subarches': SchemaItemList(),
        },
        'image': {
            'configs': SchemaItemList(),
            'initramfs': SchemaItemBoolean(),
            'initramfs-generators': SchemaItemList(),
        },
        'relations': {
        },
        'xen': {
            'versions': SchemaItemList(),
        }
    }

    def __init__(self, dirs = []):
        self._dirs = dirs
        self._readBase()

    def _readArch(self, arch):
        config = ConfigParser(self.schemas)
        config.read(self.getFiles("%s/%s" % (arch, self.config_name)))

        subarches = config['base',].get('subarches', [])
        flavours = config['base',].get('flavours', [])

        for section in iter(config):
            real = list(section)
            # TODO
            if real[-1] in subarches:
                real[0:0] = ['base', arch]
            elif real[-1] in flavours:
                real[0:0] = ['base', arch, 'none']
            else:
                real[0:0] = [real.pop()]
                if real[-1] in flavours:
                    real[1:1] = [arch, 'none']
                else:
                    real[1:1] = [arch]
            real = tuple(real)
            s = self.get(real, {})
            s.update(config[section])
            self[tuple(real)] = s

        for subarch in subarches:
            if self.has_key(('base', arch, subarch)):
                avail = self['base', arch, subarch].get('available', True)
            else:
                avail = True
            if avail:
                self._readSubarch(arch, subarch)

        base = self['base', arch]
        base['subarches'] = subarches

        if flavours:
            subarches.insert(0, 'none')
            del base['flavours']
            self['base', arch] = base
            self['base', arch, 'none'] = {'flavours': flavours}
            for flavour in flavours:
                self._readFlavour(arch, 'none', flavour)

    def _readBase(self):
        config = ConfigParser(self.schemas)
        config.read(self.getFiles(self.config_name))

        arches = config['base',]['arches']

        for section in iter(config):
            real = list(section)
            if real[-1] in arches:
                real.insert(0, 'base')
            else:
                real.insert(0, real.pop())
            self[tuple(real)] = config[section]

        for arch in arches:
            try:
                avail = self['base', arch].get('available', True)
            except KeyError:
                avail = True
            if avail:
                self._readArch(arch)

    def _readFlavour(self, arch, subarch, flavour):
        if not self.has_key(('base', arch, subarch, flavour)):
            if subarch == 'none':
                import warnings
                warnings.warn('No config entry for flavour %s, subarch none, arch %s' % (flavour, arch), DeprecationWarning)
            self['base', arch, subarch, flavour] = {}

    def _readSubarch(self, arch, subarch):
        config = ConfigParser(self.schemas)
        config.read(self.getFiles("%s/%s/%s" % (arch, subarch, self.config_name)))

        flavours = config['base',].get('flavours', [])

        for section in iter(config):
            real = list(section)
            if real[-1] in flavours:
                real[0:0] = ['base', arch, subarch]
            else:
                real[0:0] = [real.pop(), arch, subarch]
            real = tuple(real)
            s = self.get(real, {})
            s.update(config[section])
            self[tuple(real)] = s

        for flavour in flavours:
            self._readFlavour(arch, subarch, flavour)

    def getFiles(self, name):
        return [os.path.join(i, name) for i in self._dirs if i]

    def merge(self, section, arch = None, subarch = None, flavour = None):
        ret = {}
        ret.update(self.get((section,), {}))
        if arch:
            ret.update(self.get((section, arch), {}))
        if flavour and subarch and subarch != 'none':
            ret.update(self.get((section, arch, 'none', flavour), {}))
        if subarch:
            ret.update(self.get((section, arch, subarch), {}))
        if flavour:
            ret.update(self.get((section, arch, subarch, flavour), {}))
        return ret

class ConfigParser(object):
    __slots__ = '_config', 'schemas'

    def __init__(self, schemas):
        self.schemas = schemas

        from ConfigParser import RawConfigParser
        self._config = config = RawConfigParser()

    def __getitem__(self, key):
        return self._convert()[key]

    def __iter__(self):
        return iter(self._convert())

    def __str__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self._convert())

    def _convert(self):
        ret = {}
        for section in self._config.sections():
            data = {}
            for key, value in self._config.items(section):
                data[key] = value
            s1 = section.split('_')
            if s1[-1] in self.schemas:
                ret[tuple(s1)] = self.SectionSchema(data, self.schemas[s1[-1]])
            elif 'base' in self.schemas:
                import warnings
                warnings.warn('Implicit base definition: %s' % section, DeprecationWarning)
                ret[tuple(s1)] = self.SectionSchema(data, self.schemas['base'])
            else:
                ret[section] = self.Section(data)
        return ret

    def keys(self):
        return self._convert().keys()

    def read(self, data):
        return self._config.read(data)

    class Section(dict):
        def __init__(self, data):
            super(ConfigParser.Section, self).__init__(data)

        def __str__(self):
            return '<%s(%s)>' % (self.__class__.__name__, self._data)

    class SectionSchema(Section):
        __slots__ = ()

        def __init__(self, data, schema):
            for key in data.keys():
                try:
                    data[key] = schema[key](data[key])
                except KeyError: pass
            super(ConfigParser.SectionSchema, self).__init__(data)

if __name__ == '__main__':
    import sys
    config = config_reader()
    sections = config.sections()
    sections.sort()
    for section in sections:
        print "[%s]" % (section,)
        items = config[section]
        items_keys = items.keys()
        items_keys.sort()
        for item in items:
            print "%s: %s" % (item, items[item])
        print

