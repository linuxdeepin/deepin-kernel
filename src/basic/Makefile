include ../Makefile.inc

PROGS = \
	docproc \
	fixdep \
	split-include

VPATH = $(top_srcdir)/scripts/basic

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/basic/$$p'"; \
	  install -D "$$p" "$(prefix)/scripts/basic/$$p"; \
	done

