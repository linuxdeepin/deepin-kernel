PROGS = genksyms

OUTDIR = scripts/genksyms
VPATH = $(top_srcdir)/kbuild/scripts/genksyms

CFLAGS += -I$(top_srcdir)/kbuild/scripts/genksyms

genksyms: genksyms.o parse.o lex.o

lex.o: keywords.c parse.h

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@

include $(top_srcdir)/Makefile.inc
