class symbols(object):
    def __init__(self, filename = None):
        if filename is not None:
            self.read(file(filename))

    def cmp(self, new):
        symbols_ref = set(self.symbols.keys())
        symbols_new = set(new.symbols.keys())

        symbols_add = {}
        symbols_remove = {}

        symbols_change = {}

        for symbol in symbols_new - symbols_ref:
            symbols_add[symbol] = {'module': new.symbols[symbol][0]}

        for symbol in symbols_ref.intersection(symbols_new):
            module_ref, version_ref = self.symbols[symbol]
            module_new, version_new = new.symbols[symbol]

            ent = {}
            if module_ref != module_new:
                ent['module'] = module_ref, module_new
            if version_ref != version_new:
                ent['version'] = version_ref, version_new
            if ent:
                symbols_change[symbol] = ent

        for symbol in symbols_ref - symbols_new:
            symbols_remove[symbol] = {'module': self.symbols[symbol][0]}

        return symbols_add, symbols_change, symbols_remove

    def read(self, file):
        self.modules = {}
        self.symbols = {}

        for line in file.readlines():
            symbol, module, version = line.strip().split()

            symbols = self.modules.get(module, {})
            symbols[symbol] = version
            self.modules[module] = symbols
            if self.symbols.has_key(symbol):
                pass
            self.symbols[symbol] = module, version

    def read_kernel(self, file):
        self.modules = {}
        self.symbols = {}

        for line in file.readlines():
            version, symbol, module = line.strip().split('\t')

            symbols = self.modules.get(module, {})
            symbols[symbol] = version
            self.modules[module] = symbols
            if self.symbols.has_key(symbol):
                pass
            self.symbols[symbol] = module, version

    def write(self, file):
        symbols = self.symbols.items()
        symbols.sort()
        for symbol, i in symbols:
            module, version = i
            file.write("%s %s %s\n" % (symbol, module, version))

    def write_human(self, file):
        modules = self.modules.keys()
        modules.sort()
        modules.remove('vmlinux')

        file.write("Symbols in vmlinux\n\n")
        symbols = self.modules['vmlinux'].items()
        symbols.sort()
        for symbol, version in symbols:
            file.write("%-48s %s\n" % (symbol, version))

        for module in modules:
            file.write("\n\nSymbols in module %s\n\n" % module)
            symbols = self.modules[module].items()
            symbols.sort()
            for symbol, version in symbols:
                file.write("%-48s %s\n" % (symbol, version))

