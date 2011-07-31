PROGS = genksyms

OUTDIR = scripts/genksyms

top_srcdir = ../..

VPATH = $(top_srcdir)/kbuild/$(OUTDIR)

include $(top_srcdir)/debian/build/Makefile.inc

CFLAGS += -I$(VPATH)

genksyms: genksyms.o parse.o lex.o

lex.o: keywords.c parse.h

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@

clean:
	rm -f keywords.c parse.h
