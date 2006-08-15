#!/usr/bin/env python2.4

import sys
sys.path.append(sys.path[0] + "/../lib/python")

import os, os.path
from debian_linux.abi import *
from debian_linux.config import *
from debian_linux.debian import *

url_base = "http://ftp.de.debian.org/debian/"

class main(object):
    dir = None
    override_arch = None
    override_subarch = None
    override_flavour = None

    def __init__(self):
        self.log = sys.stdout.write

        if len(sys.argv) > 1:
            self.override_arch = sys.argv[1]
        if len(sys.argv) > 2:
            self.override_subarch = sys.argv[2]
        if len(sys.argv) > 3:
            self.override_flavour = sys.argv[3]

        changelog = read_changelog()
        while changelog[0]['Distribution'] == 'UNRELEASED':
            changelog.pop(0)
        changelog = changelog[0]

        self.source = changelog['Source']
        self.version = changelog['Version']['version']
        self.version_source = changelog['Version']['source']

        local_config = config_reader_arch(["debian/arch"])

        self.abiname = local_config['abi',]['abiname']
        self.version_abi = self.version + '-' + self.abiname

    def __call__(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix = 'abiupdate')
        try:
            self.log("Retreive config\n")
            config = self.get_config()
            if self.override_arch:
                arches = [self.override_arch]
            else:
                arches = config[('base',)]['arches']
            for arch in arches:
                self.update_arch(config, arch)
        finally:
            self._rmtree(self.dir)

    def _rmtree(self, dir):
        import stat
        for root, dirs, files in os.walk(dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                real = os.path.join(root, name)
                mode = os.lstat(real)[stat.ST_MODE]
                if stat.S_ISDIR(mode):
                    os.rmdir(real)
                else:
                    os.remove(real)
        os.rmdir(dir)

    def extract_package(self, filename, base = "tmp"):
        base_out = self.dir + "/" + base
        os.mkdir(base_out)
        os.system("dpkg-deb --extract %s %s" % (filename, base_out))
        return base_out

    def get_abi(self, arch, subarch, flavour):
        if subarch == 'none':
            prefix = flavour
        else:
            prefix = subarch + '-' + flavour
        filename = "linux-headers-%s-%s_%s_%s.deb" % (self.version_abi, prefix, self.version_source, arch)
        f = self.retrieve_package(filename)
        d = self.extract_package(f)
        f1 = d + "/usr/src/linux-headers-%s-%s/Module.symvers" % (self.version_abi, prefix)
        s = symbols(f1)
        self._rmtree(d)
        return s

    def get_config(self):
        filename = "linux-support-%s_%s_all.deb" % (self.version_abi, self.version_source)
        f = self.retrieve_package(filename)
        d = self.extract_package(f)
        dir = d + "/usr/src/linux-support-" + self.version_abi + "/arch"
        config = config_reader_arch([dir])
        self._rmtree(d)
        return config

    def retrieve_package(self, filename):
        import urllib2
        url = url_base + "pool/main/" + self.source[0] + "/" + self.source + "/" + filename
        filename_out = self.dir + "/" + filename
        f_in = urllib2.urlopen(url)
        f_out = file(filename_out, 'w')
        while 1:
            r = f_in.read()
            if not r:
                break
            f_out.write(r)
        return filename_out

    def save_abi(self, symbols, arch, subarch, flavour):
        out = "debian/arch/%s" % arch
        if subarch != 'none':
            out += "/%s" % subarch
        out += "/abi-%s.%s" % (self.abiname, flavour)
        symbols.write(file(out, 'w'))

    def update_arch(self, config, arch):
        if self.override_subarch:
            subarches = [self.override_subarch]
        else:
            subarches = config[('base', arch)]['subarches']
        for subarch in subarches:
            self.update_subarch(config, arch, subarch)

    def update_subarch(self, config, arch, subarch):
        config_entry = config[('base', arch, subarch)]
        if not config_entry.get('modules', True):
            return
        if self.override_flavour:
            flavours = [self.override_flavour]
        else:
            flavours = config_entry['flavours']
        for flavour in flavours:
            self.update_flavour(config, arch, subarch, flavour)

    def update_flavour(self, config, arch, subarch, flavour):
        config_entry = config[('base', arch, subarch, flavour)]
        if not config_entry.get('modules', True):
            return
        self.log("Updating ABI for arch %s, subarch %s, flavour %s: " % (arch, subarch, flavour))
        try:
            abi = self.get_abi(arch, subarch, flavour)
            self.save_abi(abi, arch, subarch, flavour)
            self.log("Ok.\n")
        except KeyboardInterrupt:
            self.log("Interrupted!\n")
            sys.exit(1)
        except Exception, e:
            self.log("FAILED! (%s)\n" % str(e))

if __name__ == '__main__':
    main()()
