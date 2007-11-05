#!/usr/bin/env python

import sys
sys.path.append('debian/lib/python')

from debian_linux.abi import *
from debian_linux.config import ConfigCoreDump

class checker(object):
    def __init__(self, dir, arch, featureset, flavour):
        self.arch, self.featureset, self.flavour = arch, featureset, flavour
        self.config = ConfigCoreDump(fp = file("debian/config.defines.dump"))
        self.filename_new = "%s/Module.symvers" % dir
        abiname = self.config['abi',]['abiname']
        self.filename_ref = "debian/abi/%s/%s_%s_%s" % (abiname, arch, featureset, flavour)

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
        config = self.config.merge('abi', self.arch, self.featureset, self.flavour)
        ignores = config.get('ignore-changes', None)
        if ignores is None:
            return set()
        return set(ignores.split())

if __name__ == '__main__':
    sys.exit(checker(*sys.argv[1:])(sys.stdout))
