import os, os.path, re, sys, textwrap, ConfigParser

__all__ = 'config_reader',

_marker = object()

class config_reader(dict):
    """
    Read configs in debian/arch and in the underlay directory.
    """

    class schema_item_boolean(object):
        def __call__(self, i):
            i = i.strip().lower()
            if i in ("true", "1"):
                return True
            if i in ("false", "0"):
                return False
            raise Error

    class schema_item_list(object):
        def __init__(self, type = "\s+"):
            self.type = type

        def __call__(self, i):
            return [j.strip() for j in re.split(self.type, i.strip())]

    schema = {
        'arches': schema_item_list(),
        'available': schema_item_boolean(),
        'flavours': schema_item_list(),
        'subarches': schema_item_list(),
    }

    config_name = "defines"

    def __init__(self, underlay = None):
        self._underlay = underlay
        self._read_base()

    def __getitem__(self, key):
        return self.get(key)

    def _get_files(self, name):
        ret = []
        if self._underlay is not None:
            ret.append(os.path.join(self._underlay, name))
        ret.append(os.path.join('debian/arch', name))
        return ret

    def _read_arch(self, arch):
        files = self._get_files("%s/%s" % (arch, self.config_name))
        config = config_parser(self.schema, files)

        subarches = config['base',].get('subarches', [])
        flavours = config['base',].get('flavours', [])

        for section in iter(config):
            real = list(section)
            if real[-1] in subarches:
                real[0:0] = ['base', arch]
            elif real[-1] in flavours:
                real[0:0] = ['base', arch, 'none']
            else:
                real[0:] = [real.pop(), arch]
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
                self._read_subarch(arch, subarch)

        if flavours:
            base = self['base', arch]
            subarches.insert(0, 'none')
            base['subarches'] = subarches
            del base['flavours']
            self['base', arch] = base
            self['base', arch, 'none'] = {'flavours': flavours}
            for flavour in flavours:
                self._read_flavour(arch, 'none', flavour)

    def _read_base(self):
        files = self._get_files(self.config_name)
        config = config_parser(self.schema, files)

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
                self._read_arch(arch)

    def _read_flavour(self, arch, subarch, flavour):
        if not self.has_key(('base', arch, subarch, flavour)):
            import warnings
            warnings.warn('No config entry for flavour %s, subarch %s, arch %s' % (flavour, subarch, arch), DeprecationWarning)
            self['base', arch, subarch, flavour] = {}

    def _read_subarch(self, arch, subarch):
        files = self._get_files("%s/%s/%s" % (arch, subarch, self.config_name))
        config = config_parser(self.schema, files)

        flavours = config['base',].get('flavours', [])

        for section in iter(config):
            real = list(section)
            if real[-1] in flavours:
                real[0:0] = ['base', arch, subarch]
            else:
                real[0:] = [real.pop(), arch, subarch]
            real = tuple(real)
            s = self.get(real, {})
            s.update(config[section])
            self[tuple(real)] = s

        for flavour in flavours:
            self._read_flavour(arch, subarch, flavour)

    def _update(self, ret, inputkey):
        for key, value in super(config_reader, self).get(tuple(inputkey), {}).iteritems():
            ret[key] = value

    def get(self, key, default = _marker):
        if isinstance(key, basestring):
            key = key,

        ret = super(config_reader, self).get(tuple(key), default)
        if ret == _marker:
            raise KeyError, key
        return ret

    def merge(self, section, *args):
        ret = {}
        for i in xrange(0, len(args) + 1):
            ret.update(self.get(tuple([section] + list(args[:i])), {}))
        if section == 'base':
            for i in ('abiname', 'arches', 'flavours', 'subarches'):
                try:
                    del ret[i]
                except KeyError: pass
        return ret

    def sections(self):
        return super(config_reader, self).keys()

class config_parser(object):
    __slots__ = 'configs', 'schema'

    def __init__(self, schema, files):
        self.configs = []
        self.schema = schema
        for file in files:
            config = ConfigParser.ConfigParser()
            config.read(file)
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

