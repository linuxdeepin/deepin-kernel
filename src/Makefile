include Makefile.inc

PROGS = \
	bin2c \
	conmakehash \
	kallsyms \
	pnmtologo

DATA = \
	Kbuild.include \
	Makefile.build \
	Makefile.clean \
	Makefile.host \
	Makefile.lib \
	Makefile.modinst \
	Makefile.modpost \
	mkversion

SCRIPTS =  \
	checkconfig.pl \
	checkincludes.pl \
	checkstack.pl \
	checkversion.pl \
	gcc-version.sh \
	gen_initramfs_list.sh \
	kernel-doc \
	Lindent \
	makelst \
	mksysmap \
	mkuboot.sh \
	namespace.pl \
	patch-kernel \
	reference_discarded.pl \
	reference_init.pl \
	setlocalversion \
	show_delta \
	ver_linux

SUBDIRS = \
	basic \
	genksyms \
	kconfig \
	mod

VPATH = $(top_srcdir)/scripts

all-local: $(PROGS)

install-local: $(PROGS)
	@list='$(PROGS)'; for p in $$list; do \
	  echo " install -D '$$p' '$(prefix)/scripts/$$p'"; \
	  install -D -m755 "$$p" "$(prefix)/scripts/$$p"; \
	done
	@list='$(SCRIPTS)'; for p in $$list; do \
	  echo " install -D '$(top_srcdir)/scripts/$$p' '$(prefix)/scripts/$$p'"; \
	  install -D -m755 "$(top_srcdir)/scripts/$$p" "$(prefix)/scripts/$$p"; \
	done
	@list='$(DATA)'; for p in $$list; do \
	  echo " install -D '$(top_srcdir)/scripts/$$p' '$(prefix)/scripts/$$p'"; \
	  install -D -m644 "$(top_srcdir)/scripts/$$p" "$(prefix)/scripts/$$p"; \
	done

