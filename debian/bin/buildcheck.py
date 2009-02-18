#!/usr/bin/python

import sys
sys.path.append('debian/lib/python')

import fnmatch
import stat

from debian_linux.abi import *
from debian_linux.config import ConfigCoreDump
from debian_linux.debian import *


class CheckAbi(object):
    def __init__(self, config, dir, arch, featureset, flavour):
        self.config = config
        self.arch, self.featureset, self.flavour = arch, featureset, flavour

        self.filename_new = "%s/Module.symvers" % dir

        changelog = Changelog(version = VersionLinux)[0]
        version = changelog.version.linux_version
        abiname = self.config['abi',]['abiname']
        self.filename_ref = "debian/abi/%s-%s/%s_%s_%s" % (version, abiname, arch, featureset, flavour)

    def __call__(self, out):
        ret = 0

        new = symbols(self.filename_new)
        try:
            ref = symbols(self.filename_ref)
        except IOError:
            out.write("Can't read ABI reference.  ABI not checked!  Continuing.\n")
            return 0

        add_info, change_info, remove_info = ref.cmp(new)
        add = set(add_info.keys())
        change = set(change_info.keys())
        remove = set(remove_info.keys())
        ignore = self._ignore(add_info, change_info, remove_info)

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
            for symbol in t:
                info = []
                if symbol in ignore:
                    info.append("ignored")
                for i in ('module', 'version', 'export'):
                    info.append("%s: %s" % (i, add_info[symbol][i]))
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))
        if change:
            out.write("\nChanged symbols:\n")
            t = list(change)
            t.sort()
            for symbol in t:
                info = []
                if symbol in ignore:
                    info.append("ignored")
                s = change_info[symbol]
                changes = s['changes']
                for i in ('module', 'version', 'export'):
                    if changes.has_key(i):
                        info.append("%s: %s -> %s" % (i, s['ref'][i], s['new'][i]))
                    else:
                        info.append("%s: %s" % (i, new[symbol][i]))
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))
        if remove:
            out.write("\nRemoved symbols:\n")
            t = list(remove)
            t.sort()
            for symbol in t:
                info = []
                if symbol in ignore:
                    info.append("ignored")
                for i in ('module', 'version', 'export'):
                    info.append("%s: %s" % (i, remove_info[symbol][i]))
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))

        return ret

    def _ignore(self, add, change, remove):
        all = set(add.keys() + change.keys() + remove.keys())
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

        s = os.stat(image)

        if s[stat.ST_SIZE] > value:
            out.write('Image too large (%d > %d)!  Refusing to continue.\n' % (s[stat.ST_SIZE], value))
            return 1

        out.write('Image fits (%d).  Continuing.\n' % value)
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
