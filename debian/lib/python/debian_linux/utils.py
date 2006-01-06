import debian, re, textwrap

class _sorted_dict(dict):
    __slots__ = ('_list')

    def __init__(self, entries = None):
        super(_sorted_dict, self).__init__()
        self._list = []
        if entries is not None:
            for key, value in entries:
                self[key] = value

    def __delitem__(self, key):
        super(_sorted_dict, self).__delitem__(key)
        self._list.remove(key)

    def iterkeys(self):
        for i in iter(self._list):
            yield i

    def iteritems(self):
        for i in iter(self._list):
            yield (i, self[i])

    def itervalues(self):
        for i in iter(self._list):
            yield self[i]

class sorted_dict(_sorted_dict):
    __slots__ = ()

    def __setitem__(self, key, value):
        super(sorted_dict, self).__setitem__(key, value)
        if key not in self._list:
            self._list.append(key)

class field_list(list):
    TYPE_WHITESPACE = object()
    TYPE_COMMATA = object()

    def __init__(self, value = None, type = TYPE_WHITESPACE):
        self.type = type
        if isinstance(value, field_list):
            self.type = value.type
            self.extend(value)
        elif isinstance(value, (list, tuple)):
            self.extend(value)
        else:
            self._extend(value)

    def __str__(self):
        if self.type is self.TYPE_WHITESPACE:
            type = ' '
        elif self.type is self.TYPE_COMMATA:
            type = ', '
        return type.join(self)

    def _extend(self, value):
        if self.type is self.TYPE_WHITESPACE:
            type = '\s'
        elif self.type is self.TYPE_COMMATA:
            type = ','
        if value is not None:
            self.extend([j.strip() for j in re.split(type, value.strip())])

    def extend(self, value):
        if isinstance(value, str):
            self._extend(value)
        else:
            super(field_list, self).extend(value)

class field_list_commata(field_list):
    def __init__(self, value = None):
        super(field_list_commata, self).__init__(value, field_list.TYPE_COMMATA)

class field_string(str):
    def __str__(self):
        return '\n '.join(self.split('\n'))

class templates(dict):
    def __init__(self, dir = None):
        if dir is None:
            self.dir = "debian/templates"
        else:
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

    def _read(self, filename):
        entries = []

        f = file("%s/%s.in" % (self.dir, filename))

        while True:
            e = debian.package()
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
                    e[last] += '\n' + line.lstrip()
                    continue
                i = line.find(':')
                if i < 0:
                    raise ValueError("Not a header, not a continuation: ``%s''" % line)
                last = line[:i]
                e[last] = line[i+1:].lstrip()
            if not e:
                break

            entries.append(e)

        return entries

class wrap(textwrap.TextWrapper):
    wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

