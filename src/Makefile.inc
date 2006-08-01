CC = gcc
CXX = g++
CFLAGS += -Wall -O2
CXXFLAGS = $(CFLAGS)

all: all-local all-recursive
install: install-local install-recursive

all-recursive install-recursive:
	@target=`echo $@ | sed s/-recursive//`; \
	list='$(SUBDIRS)'; \
	for subdir in $$list; do \
	  echo "Making $$target in $$subdir"; \
	  $(MAKE) -C $$subdir $$target \
	  || exit 1; \
	done

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/$(OUTDIR)/$$p'"; \
	  install -D -m755 "$$p" "$(prefix)/scripts/$(OUTDIR)/$$p"; \
	done
	@list='$(SCRIPTS)'; for p in $$list; do \
	  echo " install -D '$(top_srcdir)/scripts/$(OUTDIR)/$$p' '$(prefix)/scripts/$(OUTDIR)/$$p'"; \
	  install -D -m755 "$(top_srcdir)/scripts/$(OUTDIR)/$$p" "$(prefix)/scripts/$(OUTDIR)/$$p"; \
	done
	@list='$(DATA)'; for p in $$list; do \
	  echo " install -D '$(top_srcdir)/scripts/$(OUTDIR)/$$p' '$(prefix)/scripts/$(OUTDIR)/$$p'"; \
	  install -D -m644 "$(top_srcdir)/scripts/$(OUTDIR)/$$p" "$(prefix)/scripts/$(OUTDIR)/$$p"; \
	done

