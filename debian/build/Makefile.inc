top_srcdir = $(dir $(lastword $(MAKEFILE_LIST)))/../..

VPATH = $(top_srcdir)/$(OUTDIR)

SHELL = /bin/sh -e

CC = gcc
CXX = g++
CFLAGS := $(shell dpkg-buildflags --get CFLAGS) -Wall
CPPFLAGS := $(shell dpkg-buildflags --get CPPFLAGS) \
	-I$(top_srcdir)/$(OUTDIR) -I$(top_srcdir)/debian/build/$(OUTDIR) \
	-isystem $(top_srcdir)/debian/build/include
CXXFLAGS := $(shell dpkg-buildflags --get CXXFLAGS) -Wall
LDFLAGS := $(shell dpkg-buildflags --get LDFLAGS)

all: all-local all-recursive
clean: clean-local clean-recursive
install: install-local install-recursive

%-recursive:
	+@list='$(SUBDIRS)'; \
	for subdir in $$list; do \
	  echo "Making $* in $$subdir"; \
	  $(MAKE) -C $$subdir $* \
	  || exit 1; \
	done

all-local: $(PROGS)

clean-local::
	rm -f $(PROGS) *.o

install-local: install-local-progs install-local-scripts install-local-data

install-local-progs: $(PROGS)
	@for p in $^; do \
	  echo " install -m755 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -D -m755 "$$p" "$(prefix)/$(OUTDIR)/$$(basename $$p)"; \
	done

SCRIPTS_REAL = $(addprefix $(top_srcdir)/$(OUTDIR)/,$(SCRIPTS))

install-local-scripts: $(SCRIPTS_REAL)
	@for p in $^; do \
	  echo " install -m755 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -D -m755 "$$p" "$(prefix)/$(OUTDIR)/$$(basename $$p)"; \
	done

DATA_REAL = $(addprefix $(top_srcdir)/$(OUTDIR)/,$(DATA))

install-local-data: $(DATA_REAL)
	@for p in $^; do \
	  echo " install -m644 '$$p' '$(prefix)/$(OUTDIR)'"; \
	  install -D -m644 "$$p" "$(prefix)/$(OUTDIR)/$$(basename $$p)"; \
	done

