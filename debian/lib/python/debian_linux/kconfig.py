__all__ = (
    "kconfigfile",
)

class _entry(object):
    __slots__ = "name"

    def __init__(self, name):
        self.name = name

class _entry_string(_entry):
    __slots__ = "value"

    def __init__(self, name, value):
        super(_entry_string, self).__init__(name)
        self.value = value

    def __str__(self):
        return "CONFIG_%s=%s" % (self.name, self.value)

class _entry_tristate(_entry):
    __slots__ = "value"

    VALUE_NO = 0
    VALUE_YES = 1
    VALUE_MOD = 2

    def __init__(self, name, value = None):
        super(_entry_tristate, self).__init__(name)

        if value == 'n' or value is None:
            self.value = self.VALUE_NO
        elif value == 'y':
            self.value = self.VALUE_YES
        elif value == 'm':
            self.value = self.VALUE_MOD

    def __str__(self):
        conf = "CONFIG_%s" % self.name
        if self.value == self.VALUE_NO:
            return "# %s is not set" % conf
        elif self.value == self.VALUE_YES:
            return "%s=y" % conf
        elif self.value == self.VALUE_MOD:
            return "%s=m" % conf

class kconfigfile(dict):
    def __str__(self):
        ret = []
        for i in self.str_iter():
            ret.append(i)
        return '\n'.join(ret) + '\n'

    def read(self, f):
        for line in iter(f.readlines()):
            line = line.strip()
            if line.startswith("CONFIG_"):
                i = line.find('=')
                option = line[7:i]
                value = line[i+1:]
                if value in ('y', 'm'):
                    entry = _entry_tristate(option, value)
                else:
                    entry = _entry_string(option, value)
                self[option] = entry
            elif line.startswith("# CONFIG_"):
                option = line[9:-11]
                self[option] = _entry_tristate(option)
            elif line.startswith("#") or not line:
                pass
            else:
                raise RuntimeError, "Can't recognize %s" % line

    def str_iter(self):
        for key, value in self.iteritems():
            yield str(value)

