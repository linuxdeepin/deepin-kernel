SHELL = /bin/sh -e

CC = gcc
CXX = g++
CFLAGS += -Wall -O2
CXXFLAGS = $(CFLAGS)

all: all-local all-recursive
install: install-local install-recursive

all-recursive install-recursive:
	+@target=$(shell echo $@ | sed s/-recursive//); \
	list='$(SUBDIRS)'; \
	for subdir in $$list; do \
	  echo "Making $$target in $$subdir"; \
	  $(MAKE) -C $$subdir $$target \
	  || exit 1; \
	done

all-local: $(PROGS)

install-local: install-local-dir install-local-progs install-local-scripts install-local-data

install-local-dir:
	install -d "$(prefix)/$(OUTDIR)"

install-local-progs: $(PROGS)
	@for p in $^; do \
	  echo " install -m755 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -m755 "$$p" "$(prefix)/$(OUTDIR)"; \
	done

SCRIPTS_REAL = $(addprefix $(top_srcdir)/kbuild/$(OUTDIR)/,$(SCRIPTS))

install-local-scripts: $(SCRIPTS_REAL)
	@for p in $^; do \
	  echo " install -m755 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -m755 "$$p" "$(prefix)/$(OUTDIR)"; \
	done

DATA_REAL = $(addprefix $(top_srcdir)/kbuild/$(OUTDIR)/,$(DATA))

install-local-data: $(DATA_REAL)
	@for p in $^; do \
	  echo " install -m644 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -m644 "$$p" "$(prefix)/$(OUTDIR)"; \
	done

