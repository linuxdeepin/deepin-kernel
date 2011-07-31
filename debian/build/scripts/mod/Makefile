PROGS = \
	modpost \
	modpost.real-lsb-32 \
	modpost.real-lsb-64 \
	modpost.real-msb-32 \
	modpost.real-msb-64

OUTDIR = scripts/mod

top_srcdir = ../..

include $(top_srcdir)/debian/build/Makefile.inc

modpost.real-%:
	$(MAKE) -f Makefile.real TYPE=$* SOURCEDIR=$(top_srcdir)/kbuild/scripts/mod

%: %.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

modpost.h: $(top_srcdir)/kbuild/scripts/mod/modpost.c
	python ./gendef.py $< > $@

modpost.o: modpost.c modpost.h

clean:
	rm -f modpost.h
