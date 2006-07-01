PROGS = genksyms

OUTDIR = genksyms
VPATH = $(top_srcdir)/scripts/genksyms

CFLAGS += -I$(top_srcdir)/scripts/genksyms

genksyms: genksyms.o parse.o lex.o

lex.o: keywords.c parse.h

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@

include ../Makefile.inc
