import os, os.path, re, sys, textwrap

__all__ = [
    'ConfigParser',
    'ConfigReader',
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

class ConfigReader(dict):
    config_name = "defines"

    def __init__(self, dirs = []):
        self._dirs = dirs

    def __getitem__(self, key):
        return self.get(key)

    def _update(self, ret, inputkey):
        for key, value in super(ConfigReader, self).get(tuple(inputkey), {}).iteritems():
            ret[key] = value

    def getFiles(self, name):
        return [os.path.join(i, name) for i in self._dirs if i]

    def get(self, key, default = _marker):
        if isinstance(key, basestring):
            key = key,

        ret = super(ConfigReader, self).get(tuple(key), default)
        if ret == _marker:
            raise KeyError, key
        return ret

    def merge(self, section, *args):
        ret = {}
        for i in xrange(0, len(args) + 1):
            ret.update(self.get(tuple([section] + list(args[:i])), {}))
        return ret

    def sections(self):
        return super(ConfigReader, self).keys()

class ConfigReaderCore(ConfigReader):
    schema = {
        'arches': SchemaItemList(),
        'available': SchemaItemBoolean(),
        'configs': SchemaItemList(),
        'flavours': SchemaItemList(),
        'initramfs': SchemaItemBoolean(),
        'initramfs-generators': SchemaItemList(),
        'modules': SchemaItemBoolean(),
        'subarches': SchemaItemList(),
        'versions': SchemaItemList(),
    }

    def __init__(self, dirs = []):
        super(ConfigReaderCore, self).__init__(dirs)
        self._readBase()

    def _readArch(self, arch):
        files = self.getFiles("%s/%s" % (arch, self.config_name))
        config = ConfigParser(self.schema, files)

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
        files = self.getFiles(self.config_name)
        config = ConfigParser(self.schema, files)

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
        files = self.getFiles("%s/%s/%s" % (arch, subarch, self.config_name))
        config = ConfigParser(self.schema, files)

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
    __slots__ = 'configs', 'schema'

    def __init__(self, schema, files):
        self.configs = []
        self.schema = schema
        fps = []
        for i in files:
            try:
                fps.append(file(i))
            except Exception: pass
        if not fps:
            raise RuntimeError("No files found")
        for f in fps:
            import ConfigParser
            config = ConfigParser.ConfigParser()
            config.readfp(f)
            self.configs.append(config)

    def __getitem__(self, key):
        return self.items(key)

    def __iter__(self):
        return iter(self.sections())

    def items(self, section, var = {}):
        ret = {}
        section = '_'.join(section)
        exceptions = []
        for config in self.configs:
            try:
                items = config.items(section)
            except ConfigParser.NoSectionError, e:
                exceptions.append(e)
            else:
                for key, value in items:
                    try:
                        value = self.schema[key](value)
                    except KeyError: pass
                    ret[key] = value
        if len(exceptions) == len(self.configs):
            raise exceptions[0]
        return ret

    def sections(self):
        sections = []
        for config in self.configs:
            for section in config.sections():
                section = tuple(section.split('_'))
                if section not in sections:
                    sections.append(section)
        return sections

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

