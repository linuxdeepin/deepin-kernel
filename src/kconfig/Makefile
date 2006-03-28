include ../Makefile.inc

PROGS = conf

VPATH = $(top_srcdir)/scripts/kconfig

CFLAGS += -I$(top_srcdir)/scripts/kconfig

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/kconfig/$$p'"; \
	  install -D "$$p" "$(prefix)/scripts/kconfig/$$p"; \
	done

conf: conf.o zconf.tab.o

zconf.tab.c: zconf.hash.c lex.zconf.c

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@
