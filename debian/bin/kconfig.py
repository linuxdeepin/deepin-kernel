#!/usr/bin/env python2.4

import optparse, os.path, sys
from debian_linux.abi import *
from debian_linux.config import *
from debian_linux.kconfig import *

def merge(output, *config):
    config = [os.path.join('debian/arch', c) for c in config]

    kconfig = kconfigfile()
    for c in config:
        kconfig.read(file(c))
    file(output, "w").write(str(kconfig))

if __name__ == '__main__':
    sys.exit(merge(*sys.argv[1:]))
