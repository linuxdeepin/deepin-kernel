import debian, re, textwrap

class SortedDict(dict):
    __slots__ = '_list',

    def __init__(self, entries = None):
        super(SortedDict, self).__init__()
        self._list = []
        if entries is not None:
            for key, value in entries:
                self[key] = value

    def __delitem__(self, key):
        super(SortedDict, self).__delitem__(key)
        self._list.remove(key)

    def __setitem__(self, key, value):
        super(SortedDict, self).__setitem__(key, value)
        if key not in self._list:
            self._list.append(key)

    def iterkeys(self):
        for i in iter(self._list):
            yield i

    def iteritems(self):
        for i in iter(self._list):
            yield (i, self[i])

    def itervalues(self):
        for i in iter(self._list):
            yield self[i]

class Templates(dict):
    def __init__(self, dir = "debian/templates"):
        self.dir = dir

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError: pass
        ret = self._read(key)
        dict.__setitem__(self, key, ret)
        return ret

    def __setitem__(self, key, value):
        raise NotImplemented()

    def _read(self, name):
        prefix, id = name.split('.', 1)
        f = file("%s/%s.in" % (self.dir, name))

        if prefix == 'control':
            return self._readControl(f)

        return f.read()

    def _readControl(self, f):
        entries = []

        while True:
            e = debian.Package()
            last = None
            lines = []
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip('\n')
                if not line:
                    break
                if line[0] in ' \t':
                    if not last:
                        raise ValueError('Continuation line seen before first header')
                    lines.append(line.lstrip())
                    continue
                if last:
                    e[last] = '\n'.join(lines)
                i = line.find(':')
                if i < 0:
                    raise ValueError("Not a header, not a continuation: ``%s''" % line)
                last = line[:i]
                lines = [line[i+1:].lstrip()]
            if last:
                e[last] = '\n'.join(lines)
            if not e:
                break

            entries.append(e)

        return entries

class TextWrapper(textwrap.TextWrapper):
    wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

