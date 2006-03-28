include Makefile.inc

PROGS = \
	bin2c \
	conmakehash \
	kallsyms \
	pnmtologo

SCRIPTS =  \
	checkconfig.pl \
	checkincludes.pl \
	checkstack.pl \
	checkversion.pl \
	gcc-version.sh \
	gen_initramfs_list.sh \
	Kbuild.include \
	kernel-doc \
	Lindent \
	Makefile.build \
	Makefile.clean \
	Makefile.host \
	Makefile.lib \
	Makefile.modinst \
	Makefile.modpost \
	makelst \
	mksysmap \
	mkuboot.sh \
	mkversion \
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
	  install -D "$$p" "$(prefix)/scripts/$$p"; \
	done
	@list='$(SCRIPTS)'; for p in $$list; do \
	  echo " install -D '$(top_srcdir)/scripts/$$p' '$(prefix)/scripts/$$p'"; \
	  install -D "$(top_srcdir)/scripts/$$p" "$(prefix)/scripts/$$p"; \
	done

