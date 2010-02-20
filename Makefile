DATA = \
	Kbuild \
	Makefile \

SUBDIRS = \
	scripts \
	$(wildcard arch/$(SRCARCH)/scripts)

OUTDIR = .

top_srcdir = .

include $(top_srcdir)/Makefile.inc
