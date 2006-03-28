include ../Makefile.inc

PROGS = genksyms

VPATH = $(top_srcdir)/scripts/genksyms

CFLAGS += -I$(top_srcdir)/scripts/genksyms

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/genksyms/$$p'"; \
	  install -D "$$p" "$(prefix)/scripts/genksyms/$$p"; \
	done

genksyms: genksyms.o parse.o lex.o

lex.o: keywords.c parse.h

%.c: %.c_shipped
	ln -s $< $@

%.h: %.h_shipped
	ln -s $< $@
