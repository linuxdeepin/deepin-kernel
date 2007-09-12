import os, shutil

class Operation(object):
    def __init__(self, name, fp, data):
        self.name, self.fp, self.data = name, fp, data

    def __call__(self, dir = '.', reverse = False):
        try:
            if not reverse:
                self.do(dir)
            else:
                self.do_reverse(dir)
            self._log(True)
        except:
            self._log(False)
            raise

    def _log(self, result):
        if result:
            s = "OK"
        else:
            s = "FAIL"
        print """  (%s) %-4s %s""" % (self.operation, s, self.name)

    def do(self, dir):
        raise NotImplementedError

    def do_reverse(self, dir):
        raise NotImplementedError

class OperationPatch(Operation):
    def _call(self, dir, extraargs):
        cmdline = "cd %s; patch -p1 -f -s -t --no-backup-if-mismatch %s" % (dir, extraargs)
        f = os.popen(cmdline, 'wb')
        shutil.copyfileobj(self.fp, f)
        if f.close():
            raise RuntimeError("Patch failed")

    def patch_push(self, dir):
        self._call(dir, '--fuzz=1')

    def patch_pop(self, dir):
        self._call(dir, '-R')

class OperationPatchPush(OperationPatch):
    operation = '+'

    do = OperationPatch.patch_push
    do_reverse = OperationPatch.patch_pop

class OperationPatchPop(OperationPatch):
    operation = '-'

    do = OperationPatch.patch_pop
    do_reverse = OperationPatch.patch_push

class OperationRemoveFiles(Operation):
    operation = 'X'

    def do(self, dir):
        for line in self.fp:
            line = line.strip()
            if not line or line[0] == '#':
                continue

            os.unlink(os.path.join(dir, line))

class PatchSeries(list):
    operations = {
        '+': OperationPatchPush,
        '-': OperationPatchPop,
        'X': OperationRemoveFiles,
    }

    def __init__(self, name, root, fp):
        self.name, self.root = name, root

        from gzip import GzipFile
        from bz2 import BZ2File

        for line in fp:
            line = line.strip()

            if not len(line) or line[0] == '#':
                continue

            items = line.split(' ')
            operation, filename = items[:2]
            data = dict(i.split('=', 1) for i in items[2:])

            if operation in self.operations:
                f = os.path.join(self.root, filename)
                for suffix, cls in (('', file), ('.bz2', BZ2File), ('.gz', GzipFile)):
                    f1 = f + suffix
                    if os.path.exists(f1):
                        fp = cls(f1)
                        break
                else:
                    raise RuntimeError("Can't find patch %s for series %s" % (filename, self.name))
            else:
                raise RuntimeError('Undefined operation "%s" in series %s' % (operation, name))

            self.append(self.operations[operation](filename, fp, data))

    def __call__(self, cond = bool, dir = '.', reverse = False):
        if not reverse:
            for i in self:
                if cond(i):
                    i(dir = dir, reverse = False)
        else:
            for i in self[::-1]:
                if cond(i):
                    i(dir = dir, reverse = True)

    def __repr__(self):
        return '<%s object for %s>' % (self.__class__.__name__, self.name)

