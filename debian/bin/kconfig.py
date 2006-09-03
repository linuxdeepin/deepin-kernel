#!/usr/bin/env python2.4

import sys
from debian_linux.abi import *
from debian_linux.config import *
from debian_linux.kconfig import *

class checker(object):
    def __init__(self, arch, subarch, flavour):
        self.config = config_reader_arch(["debian/arch"])

        self.config = ["debian/arch/config"]
        self.config_arch = ["debian/arch/%s/config" % arch]
        if subarch == 'none':
            self.config_subarch = []
            self.config_flavour = ["debian/arch/%s/config.%s" % (arch, flavour)]
        else:
            self.config_subarch = ["debian/arch/%s/%s/config" % (arch, subarch)]
            self.config_flavour = ["debian/arch/%s/%s/config.%s" % (arch, subarch, flavour)]

    def __call__(self, out):
        config = []
        config.extend(self.config)
        config.extend(self.config_arch)
        config.extend(self.config_subarch)
        config.extend(self.config_flavour)

        kconfig = kconfigfile()
        for c in config:
            kconfig.read(file(c))

        out.write(str(kconfig))

if __name__ == '__main__':
    sys.exit(checker(*sys.argv[1:])(sys.stdout))
