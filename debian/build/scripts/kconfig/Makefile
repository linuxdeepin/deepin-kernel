PROGS = conf

include ../../Makefile.inc

conf: conf.o zconf.tab.o

zconf.tab.c: zconf.hash.c zconf.lex.c

%.c: %.c_shipped
	ln -sf $< $@

%.h: %.h_shipped
	ln -sf $< $@

clean:
	rm -f zconf.tab.c zconf.hash.c zconf.lex.c
