import debian, re, os, textwrap

_marker = object

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
    def __init__(self, dirs = ["debian/templates"]):
        self.dirs = dirs

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        raise NotImplemented()

    def _read(self, name):
        prefix, id = name.split('.', 1)

        for dir in self.dirs:
            filename = "%s/%s.in" % (dir, name)
            if os.path.exists(filename):
                f = file(filename)
                if prefix == 'control':
                    return self._read_control(f)
                return f.read()

    def _read_control(self, f):
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

    def get(self, key, default = _marker):
        ret = super(Templates, self).get(key, _marker)
        if ret is not _marker:
            return ret
        value = self._read(key)
        if value is None:
            if default is _marker:
                raise KeyError(key)
            return default
        super(Templates, self).__setitem__(key, value)
        return value

class TextWrapper(textwrap.TextWrapper):
    wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

