from collections import OrderedDict

__all__ = (
    "KconfigFile",
)


class EntryString(object):
    __slots__ = "name", "value"

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "CONFIG_%s=%s" % (self.name, self.value)


class EntryTristate(object):
    __slots__ = "name", "value"

    VALUE_NO = 0
    VALUE_YES = 1
    VALUE_MOD = 2

    def __init__(self, name, value=None):
        self.name = name
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


class KconfigFile(OrderedDict):
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
                value = line[i + 1:]
                self.set(option, value)
            elif line.startswith("# CONFIG_"):
                option = line[9:-11]
                self.set(option, 'n')
            elif line.startswith("#") or not line:
                pass
            else:
                raise RuntimeError("Can't recognize %s" % line)

    def set(self, key, value):
        if value in ('y', 'm', 'n'):
            entry = EntryTristate(key, value)
        else:
            entry = EntryString(key, value)
        self[key] = entry

    def str_iter(self):
        for key, value in self.iteritems():
            yield str(value)
