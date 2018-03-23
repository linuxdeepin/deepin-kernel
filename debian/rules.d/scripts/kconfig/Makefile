PROGS = conf

include $(top_rulesdir)/Makefile.inc

conf: conf.o zconf.tab.o

zconf.tab.c: kconf_id.c zconf.lex.c

%.lex.c: %.l
	flex -o$@ -L $<

%.tab.c: %.y
	bison -o$@ -t -l $<
