#!/usr/bin/env python2.4

import optparse, os.path, sys
from debian_linux.abi import *
from debian_linux.config import *
from debian_linux.kconfig import *

class checker(object):
    parser = optparse.OptionParser()
    parser.add_option('-b', '--base', dest = 'base', default = "debian/arch")
    parser.add_option('-o', '--output', dest = 'output')

    def __init__(self):
        options, args = self.parser.parse_args()

        self.base = options.base
        self.output = options.output

        arch, subarch, flavour = args

        config = config_reader_arch([self.base])

        self.config = self._get_config(config, ["config"])
        self.config_arch = self._get_config(config, ["%s/config" % arch], arch)
        if subarch == 'none':
            self.config_subarch = []
            self.config_flavour = self._get_config(config, ["%s/config.%s" % (arch, flavour)], arch, subarch, flavour)
        else:
            self.config_subarch = self._get_config(config, ["%s/%s/config" % (arch, subarch)], arch, subarch)
            self.config_flavour = self._get_config(config, ["%s/%s/config.%s" % (arch, subarch, flavour)], arch, subarch, flavour)

    def __call__(self):
        config = []
        config.extend(self.config)
        config.extend(self.config_arch)
        config.extend(self.config_subarch)
        config.extend(self.config_flavour)
        config = [os.path.join(self.base, c) for c in config]

        if self.output:
            kconfig = kconfigfile()
            for c in config:
                kconfig.read(file(c))
            file(self.output, "w").write(str(kconfig))
        else:
            print '\n'.join(config)

    def _get_config(self, config, default, *entry_name):
        entry_real = ('image',) + entry_name
        entry = config.get(entry_real, None)
        if entry is None:
            return default
        configs = entry.get('configs', None)
        if configs is None:
            return default
        return configs

if __name__ == '__main__':
    sys.exit(checker()())
