CC = gcc
CXX = g++
CFLAGS = -Wall -W -O2
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

