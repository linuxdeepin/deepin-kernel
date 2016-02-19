PROGS = genksyms

include ../../Makefile.inc

genksyms: genksyms.o parse.tab.o lex.lex.o

lex.lex.o: keywords.hash.c parse.tab.h

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@

clean:
	rm -f keywords.hash.c parse.tab.c parse.tab.h
