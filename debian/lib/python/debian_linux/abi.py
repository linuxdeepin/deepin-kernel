class symbols(dict):
    def __init__(self, filename = None):
        self.modules = {}
        if filename is not None:
            self.read(file(filename))

    def cmp(self, new):
        symbols_ref = set(self.keys())
        symbols_new = set(new.keys())

        symbols_add = {}
        symbols_remove = {}

        symbols_change = {}

        for symbol in symbols_new - symbols_ref:
            symbols_add[symbol] = new[symbol]

        for symbol in symbols_ref.intersection(symbols_new):
            symbol_ref = self[symbol]
            symbol_new = new[symbol]

            ent = {'ref': symbol_ref, 'new': symbol_new, 'changes': {}}
            for i in ('module', 'version', 'export'):
                if symbol_ref[i] != symbol_new[i]:
                    ent['changes'][i] = {'ref': symbol_ref, 'new': symbol_new}
            if ent['changes']:
                symbols_change[symbol] = ent

        for symbol in symbols_ref - symbols_new:
            symbols_remove[symbol] = self[symbol]

        return symbols_add, symbols_change, symbols_remove

    def read(self, file):
        for line in file.readlines():
            version, symbol, module, export = line.strip().split()

            if self.has_key(symbol):
                pass
            symbols = self.modules.get(module, set())
            symbols.add(symbol)
            self.modules[module] = symbols
            self[symbol] = {'symbol': symbol, 'module': module, 'version': version, 'export': export}

    def write(self, file):
        symbols = self.items()
        symbols.sort()
        for symbol, info in symbols:
            file.write("%(version)s %(symbol)s %(module)s %(export)s\n" % info)

