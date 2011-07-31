PROGS = conf

OUTDIR = scripts/kconfig

top_srcdir = ../..

VPATH = $(top_srcdir)/$(OUTDIR)

include $(top_srcdir)/debian/build/Makefile.inc

CFLAGS += -I$(VPATH)

conf: conf.o zconf.tab.o

zconf.tab.c: zconf.hash.c lex.zconf.c

%.c: %.c_shipped
	ln -sf $< $@

%.h: %.h_shipped
	ln -sf $< $@

clean:
	rm -f zconf.tab.c zconf.hash.c lex.zconf.c
