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
	mkversion \
	module-common.lds

SCRIPTS =  \
	checkincludes.pl \
	checkstack.pl \
	checkversion.pl \
	gcc-version.sh \
	gcc-x86_32-has-stack-protector.sh \
	gcc-x86_64-has-stack-protector.sh \
	gen_initramfs_list.sh \
	kernel-doc \
	Lindent \
	makelst \
	mksysmap \
	mkuboot.sh \
	namespace.pl \
	patch-kernel \
	setlocalversion \
	ver_linux

SUBDIRS = \
	basic \
	genksyms \
	kconfig \
	mod

OUTDIR = scripts

top_srcdir = ..

VPATH = $(top_srcdir)/kbuild/scripts

include $(top_srcdir)/Makefile.inc
