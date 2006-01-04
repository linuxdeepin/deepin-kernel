#!/usr/bin/env python2.4

import os.path, sys
from warnings import warn
import debian_linux

_default_home = "@home@"
_default_revisions = "@revisions@"
_default_source = "@source@"

class series(list):
    def __init__(self, name, home, reverse = False):
        self.name = name
        self.reverse = reverse

        filename = os.path.join(home, 'series', name)
        if not os.path.exists(filename):
            raise RuntimeError, "Can't find series file for %s" % name

        f = file(filename)
        for line in f.readlines():
            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            items = line.split(' ')
            operation, patch = items

            if operation in ('+', '-'):
                patchfile = os.path.join(home, patch)
                for suffix, type in (('', 0), ('.bz2', 1), ('.gz', 2)):
                    if os.path.exists(patchfile + suffix):
                        patchinfo = patchfile + suffix, type
                        break
                else:
                    raise RuntimeError, "Can't find patch %s for series %s" % (patchfile, name)
            elif operation in ('X',):
                backup = patch + ".bak"
                if not os.path.exists(patch) and not os.path.exists(backup):
                    raise RuntimeError, "Can't find neither original nor backup file %s for series %s" % (patch, name)
                patchinfo = patch, backup
            else:
                raise RuntimeError, 'Undefined operation "%s" in series %s' % (operation, name)

            self.append((operation, patch, patchinfo))

    def __repr__(self):
        return '<%s object for %s>' % (self.__class__.__name__, self.name)

    def apply(self):
        if self.reverse:
            for operation, patch, patchinfo in self[::-1]:
                if operation == '.':
                    print """\
  (.) IGNORED   %s\
""" % patch
                elif operation == '+':
                    self.patch_deapply(patch, patchinfo)
                elif operation == '-':
                    self.patch_apply(patch, patchinfo)
                elif operation == 'X':
                    os.rename(patchinfo[1], patchinfo[0])
                    print """\
  (X) RESTORED  %s\
""" % patch
            print "--> %s fully unapplied." % self.name

        else:
            for operation, patch, patchinfo in self:
                if operation == '.':
                    print """\
  (.) IGNORED   %s\
""" % patch
                elif operation == '+':
                    self.patch_apply(patch, patchinfo)
                elif operation == '-':
                    self.patch_deapply(patch, patchinf)
                elif operation == 'X':
                    os.rename(patchinfo[0], patchinfo[1])
                    print """\
  (X) REMOVED   %s\
""" % patch
            print "--> %s fully applied." % self.name

    def patch_apply(self, patch, patchinfo):
        ret = self.patch_call(patchinfo, '--fuzz=1')
        if ret == 0:
            print """\
  (+) OK        %s\
""" % patch
        else:
            print """\
  (+) FAIL      %s\
""" % patch
            raise SystemExit, 1

    def patch_call(self, patchinfo, patchargs):
        patchfile, type = patchinfo
        cmdline = []
        if type == 0:
            cmdline.append('cat')
        elif type == 1:
            cmdline.append('bzcat')
        elif type == 2:
            cmdline.append('zcat')
        cmdline.append(patchfile + ' | patch -p1 -f -s -t --no-backup-if-mismatch')
        cmdline.append(patchargs)
        return os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '-c', ' '.join(cmdline)])

    def patch_deapply(self, patch, patchinfo):
        ret = self.patch_call(patchinfo, '-R')
        if ret == 0:
            print """\
  (-) OK        %s\
""" % patch
        else:
            print """\
  (-) FAIL      %s\
""" % patch
            raise SystemExit, 1

    @staticmethod
    def read_all(s, home, reverse = False):
        ret = []

        for name in s:
            filename = os.path.join(home, 'series', name)
            if not os.path.exists(filename):
                warn("Can't find series file for %s" % name)
            else:
                i = series(name, home, reverse)
                ret.append(i)

        return ret

class series_extra(series):
    def __init__(self, name, home, extra, reverse = False):
        self.extra = extra
        self.extra_used = ()
        self.name = name
        self.reverse = reverse

        filename = os.path.join(home, 'series', name + '-extra')
        if not os.path.exists(filename):
            raise RuntimeError, "Can't find series file for %s" % name

        f = file(filename)
        for line in f.readlines():
            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            items = line.split(' ')
            operation, patch = items[:2]

            if operation in ('+', '-'):
                patchfile = os.path.join(home, patch)
                for suffix, type in (('', 0), ('.bz2', 1), ('.gz', 2)):
                    if os.path.exists(patchfile + suffix):
                        patchinfo = patchfile + suffix, type
                        break
                else:
                    raise RuntimeError, "Can't find patch %s for series %s" % (patchfile, name)
            else:
                raise RuntimeError, 'Undefined operation "%s" in series %s' % (operation, name)

            extra = {}
            for s in items[2:]:
                s = tuple(s.split('_'))
                if len(s) > 3:
                    raise RuntimeError, "parse error"
                if len(s) == 3:
                    raise RuntimeError, "Patch per flavour is not supported currently"
                extra[s] = True
            if not self._check_extra(extra):
                operation = '.'

            self.append((operation, patch, patchinfo))

    def _check_extra(self, extra):
        for i in (1, 2, 3):
            t = tuple(self.extra[:i])
            if extra.has_key(t):
                if i > len(self.extra_used):
                    self.extra_used = t
                return True
        return False

    @staticmethod
    def read_all(s, home, extra, reverse = False):
        ret = []

        for name in s:
            filename = os.path.join(home, 'series', name + '-extra')
            if not os.path.exists(filename):
                warn("Can't find series file for %s" % name)
            else:
                i = series_extra(name, home, extra, reverse)
                ret.append(i)

        return ret

class version(object):
    __slots__ = "upstream", "revision"

    def __init__(self, string = None):
        if string is not None:
            t = debian_linux.parse_version(string)
            self.upstream = t['source_upstream']
            self.revision = t['debian']

    def __str__(self):
        return "%s-%s" % (self.upstream, self.revision)

class version_file(object):
    _file = 'version.Debian'
    extra = ()
    in_progress = False

    def __init__(self, ver = None, overwrite = False):
        if overwrite:
            self._read(ver)
        elif os.path.exists(self._file):
            s = file(self._file).readline().strip()
            self._read(s)
        elif ver:
            warn('No %s file, assuming pristine Linux %s' % (self._file, ver.upstream))
            self.version = version()
            self.version.upstream = ver.upstream
            self.version.revision = '0'
        else:
            raise RuntimeError, "Not possible to determine version"

    def __str__(self):
        if self.in_progress:
            return "unstable"
        if self.extra:
            return "%s %s" % (self.version, '_'.join(self.extra))
        return str(self.version)

    def _read(self, s):
        list = s.split(' ')
        if len(list) > 2:
            raise RuntimeError, "Can't parse %s" % self._file
        try:
            self.version = version(list[0])
        except ValueError:
            raise RuntimeError, 'Can\'t read version in %s: "%s"' % (self._file, list[0])
        if len(list) == 2:
            self.extra = tuple(list[1].split('_'))

    def _write(self):
        file(self._file, 'w').write('%s\n' % self)

    def begin(self):
        self.in_progress = True
        self._write()

    def commit(self, version = None, extra = None):
        self.in_progress = False
        if version is not None:
            self.version = version
        if extra is not None:
            self.extra = extra
        self._write()

def main():
    options, args = parse_options()

    if len(args) > 1:
        print "Too much arguments"
        return

    home = options.home
    revisions = ['0'] + options.revisions.split()
    source = version(options.source)
    if len(args) == 1:
        target = version(args[0])
    else:
        target = source

    if options.current is not None:
        vfile = version_file(options.current, True)
    else:
        vfile = version_file(source)
    current = vfile.version
    current_extra = vfile.extra

    target_extra = []
    if options.arch: target_extra.append(options.arch)
    if options.subarch: target_extra.append(options.subarch)
    if options.flavour: target_extra.append(options.flavour)
    target_extra = tuple(target_extra)

    if current.revision not in revisions:
        raise RuntimeError, "Current revision is not in our list of revisions"
    if target.revision not in revisions:
        raise RuntimeError, "Target revision is not in our list of revisions"

    if current.revision == target.revision and current_extra == target_extra:
        print "Nothing to do"
        return

    current_index = revisions.index(current.revision)
    target_index = revisions.index(target.revision)

    if current_extra:
        consider = revisions[current_index:0:-1]
        s = series_extra.read_all(consider, home, current_extra, reverse = True)
        vfile.begin()
        for i in s:
            i.apply()
        vfile.commit(current, ())

    if current_index < target_index:
        consider = revisions[current_index + 1:target_index + 1]
        s = series.read_all(consider, home)
        vfile.begin()
        for i in s:
            i.apply()
        vfile.commit(target, ())
    elif current_index > target_index:
        consider = revisions[current_index:target_index:-1]
        s = series.read_all(consider, home, reverse = True)
        vfile.begin()
        for i in s:
            i.apply()
        vfile.commit(target, ())

    if target_extra:
        consider = revisions[1:target_index + 1]
        s = series_extra.read_all(consider, home, target_extra)
        real_extra = ()
        for i in s:
            t = i.extra_used
            if len(t) > len(real_extra):
                real_extra = t
        vfile.begin()
        for i in s:
            i.apply()
        vfile.commit(target, real_extra)

def parse_options():
    from optparse import OptionParser
    parser = OptionParser(
        usage = "%prog [OPTION]... [TARGET]",
    )
    parser.add_option(
        '-a', '--arch',
        dest = 'arch',
        help = "arch",
    )
    parser.add_option(
        '-f', '--flavour',
        dest = 'flavour',
        help = "flavour",
    )
    parser.add_option(
        '-s', '--subarch',
        dest = 'subarch',
        help = "subarch",
    )
    parser.add_option(
        '-C', '--overwrite-current',
        dest = 'current',
        help = "overwrite current",
    )
    parser.add_option(
        '-H', '--overwrite-home',
        default = _default_home, dest = 'home',
        help = "overwrite home [default: %default]",
    )
    parser.add_option(
        '-R', '--overwrite-revisions',
        default = _default_revisions, dest = 'revisions',
        help = "overwrite revisions [default: %default]",
    )
    parser.add_option(
        '-S', '--overwrite-source',
        default = _default_source, dest = 'source',
        help = "overwrite source [default: %default]",
    )

    options, args = parser.parse_args()

    if options.arch is None and options.subarch is not None:
        raise RuntimeError('You specified a subarch without an arch, this is not really working')
    if options.subarch is None and options.flavour is not None:
        raise RuntimeError('You specified a flavour without a subarch, this is not really working')

    return options, args

if __name__ == '__main__':
    def showwarning(message, category, filename, lineno):
        sys.stderr.write("Warning: %s\n" % message)
    import warnings
    warnings.showwarning = showwarning
    try:
        main()
    except RuntimeError, e:
        sys.stderr.write("Error: %s\n" % e)
        raise SystemExit, 1

