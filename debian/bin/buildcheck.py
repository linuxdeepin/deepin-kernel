#!/usr/bin/python

import sys
sys.path.append('debian/lib/python')

import fnmatch
import stat

from debian_linux.abi import Symbols
from debian_linux.config import ConfigCoreDump
from debian_linux.debian import *


class CheckAbi(object):
    class SymbolInfo(object):
        def __init__(self, symbol):
            self.symbol = symbol

        def write(self, out, ignored):
            info = []
            if ignored:
                info.append("ignored")
            for i in ('module', 'version', 'export'):
                info.append("%s: %s" % (i, getattr(self.symbol, i)))
            out.write("%-48s %s\n" % (self.symbol.name, ", ".join(info)))

    class SymbolChangeInfo(object):
        def __init__(self, symbol_ref, symbol_new):
            self.symbol_ref, self.symbol_new = symbol_ref, symbol_new

        def write(self, out, ignored):
            info = []
            if ignored:
                info.append("ignored")
            for i in ('module', 'version', 'export'):
                d_ref = getattr(self.symbol_ref, i)
                d_new = getattr(self.symbol_new, i)
                if d_ref != d_new:
                    info.append("%s: %s -> %s" % (i, d_ref, d_new))
                else:
                    info.append("%s: %s" % (i, d_new))
            out.write("%-48s %s\n" % (self.symbol_new.name, ", ".join(info)))

    def __init__(self, config, dir, arch, featureset, flavour):
        self.config = config
        self.arch, self.featureset, self.flavour = arch, featureset, flavour

        self.filename_new = "%s/Module.symvers" % dir

        changelog = Changelog(version=VersionLinux)[0]
        version = changelog.version.linux_version
        abiname = self.config['abi',]['abiname']
        self.filename_ref = "debian/abi/%s-%s/%s_%s_%s" % (version, abiname, arch, featureset, flavour)

    def __call__(self, out):
        ret = 0

        new = Symbols(open(self.filename_new))
        try:
            ref = Symbols(open(self.filename_ref))
        except IOError:
            out.write("Can't read ABI reference.  ABI not checked!  Continuing.\n")
            return 0

        symbols, add, change, remove = self._cmp(ref, new)

        ignore = self._ignore(symbols.keys())

        add_effective = add - ignore
        change_effective = change - ignore
        remove_effective = remove - ignore

        if change_effective or remove_effective:
            out.write("ABI has changed!  Refusing to continue.\n")
            ret = 1
        elif change or remove:
            out.write("ABI has changed but all changes have been ignored.  Continuing.\n")
        elif add_effective:
            out.write("New symbols have been added.  Continuing.\n")
        elif add:
            out.write("New symbols have been added but have been ignored.  Continuing.\n")
        else:
            out.write("No ABI changes.\n")

        if add:
            out.write("\nAdded symbols:\n")
            t = list(add)
            t.sort()
            for name in t:
                symbols[name].write(out, name in ignore)

        if change:
            out.write("\nChanged symbols:\n")
            t = list(change)
            t.sort()
            for name in t:
                symbols[name].write(out, name in ignore)

        if remove:
            out.write("\nRemoved symbols:\n")
            t = list(remove)
            t.sort()
            for name in t:
                symbols[name].write(out, name in ignore)

        return ret

    def _cmp(self, ref, new):
        ref_names = set(ref.keys())
        new_names = set(new.keys())

        add = set()
        change = set()
        remove = set()

        symbols = {}

        for name in new_names - ref_names:
            add.add(name)
            symbols[name] = self.SymbolInfo(new[name])

        for name in ref_names.intersection(new_names):
            s_ref = ref[name]
            s_new = new[name]

            if s_ref != s_new:
                change.add(name)
                symbols[name] = self.SymbolChangeInfo(s_ref, s_new)

        for name in ref_names - new_names:
            remove.add(name)
            symbols[name] = self.SymbolInfo(ref[name])

        return symbols, add, change, remove

    def _ignore(self, all):
        # TODO: let config merge this lists
        configs = []
        configs.append(self.config.get(('abi', self.arch, self.featureset, self.flavour), {}))
        configs.append(self.config.get(('abi', self.arch, None, self.flavour), {}))
        configs.append(self.config.get(('abi', self.arch, self.featureset), {}))
        configs.append(self.config.get(('abi', self.arch), {}))
        configs.append(self.config.get(('abi',), {}))
        ignores = set()
        for config in configs:
            ignores.update(config.get('ignore-changes', []))
        filtered = set()
        for m in ignores:
            filtered.update(fnmatch.filter(all, m))
        return filtered
 

class CheckImage(object):
    def __init__(self, config, dir, arch, featureset, flavour):
        self.dir = dir
        self.arch, self.featureset, self.flavour = arch, featureset, flavour

        self.config_entry_build = config.merge('build', arch, featureset, flavour)
        self.config_entry_image = config.merge('image', arch, featureset, flavour)

    def __call__(self, out):
        image = self.config_entry_build.get('image-file')

        if not image:
            # TODO: Bail out
            return 0

        image = os.path.join(self.dir, image)

        fail = 0

        fail |= self.check_size(out, image)

        return fail

    def check_size(self, out, image):
        value = self.config_entry_image.get('check-size')

        if not value:
            return 0

        value = int(value)

        size = os.stat(image)[stat.ST_SIZE]

        if size > value:
            out.write('Image too large (%d > %d)!  Refusing to continue.\n' % (size, value))
            return 1

        out.write('Image fits (%d <= %d).  Continuing.\n' % (size, value))
        return 0


class Main(object):
    def __init__(self, dir, arch, featureset, flavour):
        self.args = dir, arch, featureset, flavour

        self.config = ConfigCoreDump(fp=file("debian/config.defines.dump"))

    def __call__(self):
        fail = 0

        for c in CheckAbi, CheckImage:
            fail |= c(self.config, *self.args)(sys.stdout)

        return fail


if __name__ == '__main__':
    sys.exit(Main(*sys.argv[1:])())
