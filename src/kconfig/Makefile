PROGS = conf

OUTDIR = kconfig
VPATH = $(top_srcdir)/scripts/kconfig

CFLAGS += -I$(top_srcdir)/scripts/kconfig

conf: conf.o zconf.tab.o

zconf.tab.c: zconf.hash.c lex.zconf.c

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@

include ../Makefile.inc
