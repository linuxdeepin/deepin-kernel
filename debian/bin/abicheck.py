#!/usr/bin/env python2.4

import sys
from debian_linux.abi import *
from debian_linux.config import *

class checker(object):
    def __init__(self, dir, arch, subarch, flavour):
        self.config = config_reader(["debian/arch"])
        self.filename_new = "%s/Module.symvers" % dir
        abiname = self.config['abiname',]['abiname']
        if subarch == 'none':
            self.filename_ref = "debian/arch/%s/abi-%s.%s" % (arch, abiname, flavour)
        else:
            self.filename_ref = "debian/arch/%s/%s/abi-%s.%s" % (arch, subarch, abiname, flavour)

    def __call__(self, out):
        ret = 0

        new = symbols()
        new.read_kernel(file(self.filename_new))
        try:
            ref = symbols(self.filename_ref)
        except IOError:
            out.write("Can't read ABI reference.  ABI not checked!  Continuing.\n")
            return 0

        add_info, change_info, remove_info = ref.cmp(new)
        add = set(add_info.keys())
        change = set(change_info.keys())
        remove = set(remove_info.keys())
        add_ignore, change_ignore, remove_ignore = self._ignore(add_info, change_info, remove_info)

        add_effective = add - add_ignore
        change_effective = change - change_ignore
        remove_effective = remove - remove_ignore

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
                if symbol in add_ignore:
                    info.append("ignored")
                info.append("module: %s" % add_info[symbol]['module'])
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))
        if change:
            out.write("\nChanged symbols:\n")
            t = list(change)
            t.sort()
            for symbol in t:
                info = []
                if symbol in change_ignore:
                    info.append("ignored")
                if change_info[symbol].has_key('module'):
                    info.append("module: %s -> %s" % change_info[symbol]['module'])
                if change_info[symbol].has_key('version'):
                    info.append("version: %s -> %s" % change_info[symbol]['version'])
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))
        if remove:
            out.write("\nRemoved symbols:\n")
            t = list(remove)
            t.sort()
            for symbol in t:
                info = []
                if symbol in remove_ignore:
                    info.append("ignored")
                info.append("module: %s" % remove_info[symbol]['module'])
                out.write("%-48s %s\n" % (symbol, ", ".join(info)))

        return ret

    def _ignore(self, add, change, remove):
        return set(), set(), set()

if __name__ == '__main__':
    sys.exit(checker(*sys.argv[1:])(sys.stdout))
