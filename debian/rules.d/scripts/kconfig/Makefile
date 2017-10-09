PROGS = conf

include $(top_rulesdir)/Makefile.inc

conf: conf.o zconf.tab.o

zconf.tab.c: kconf_id.c zconf.lex.c

%.c: %.c_shipped
	ln -sf $< $@

%.h: %.h_shipped
	ln -sf $< $@
