PROGS = \
	modpost \
	modpost.real-lsb-32 \
	modpost.real-lsb-64 \
	modpost.real-msb-32 \
	modpost.real-msb-64

OUTDIR = mod

modpost.real-%:
	$(MAKE) -f Makefile.real TYPE=$* SOURCEDIR=$(top_srcdir)/kbuild/scripts/mod

%: %.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

include ../Makefile.inc

clean:
	rm $(PROGS) *.o

