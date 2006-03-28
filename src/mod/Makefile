include ../Makefile.inc

PROGS = modpost

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/mod/$$p'"; \
	  install -D "$$p" "$(prefix)/scripts/mod/$$p"; \
	done

modpost: elf.o modpost.o module.o module_devicetable.o module_devicetable_impl_2_6_16.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.cpp %.hpp endian.hpp

