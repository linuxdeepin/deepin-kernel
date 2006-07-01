include ../Makefile.inc

PROGS = modpost

OUTDIR = mod

modpost: elf.o modpost.o module.o module_devicetable.o module_devicetable_impl_2_6_16.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.cpp %.hpp endian.hpp

clean:
	rm $(PROGS) *.o
