PROGS = \
	modpost \
	modpost.real-lsb-32 \
	modpost.real-lsb-64 \
	modpost.real-msb-32 \
	modpost.real-msb-64

OUTDIR = scripts/mod

include ../../Makefile.inc

modpost.real-%:
	$(MAKE) -f Makefile.real TYPE=$* SOURCEDIR=$(top_srcdir)/scripts/mod

%: %.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

modpost.h: $(top_srcdir)/scripts/mod/modpost.c
	python ./gendef.py $< > $@

modpost.o: modpost.c modpost.h

clean:
	rm -f modpost.h real-*/devicetable-offsets.*
