#!/usr/bin/env python

import optparse, os.path, sys
from debian_linux.kconfig import *

def merge(output, *config):
    kconfig = KconfigFile()
    for c in config:
        kconfig.read(file(c))
    file(output, "w").write(str(kconfig))

if __name__ == '__main__':
    sys.exit(merge(*sys.argv[1:]))
