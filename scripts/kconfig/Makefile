PROGS = conf

OUTDIR = scripts/kconfig
VPATH = $(top_srcdir)/kbuild/scripts/kconfig

CFLAGS += -I$(top_srcdir)/kbuild/scripts/kconfig

conf: conf.o zconf.tab.o

zconf.tab.c: zconf.hash.c lex.zconf.c

%.c: %.c_shipped
	ln -sf $< $@

%.h: %.h_shipped
	ln -sf $< $@

include $(top_srcdir)/Makefile.inc
