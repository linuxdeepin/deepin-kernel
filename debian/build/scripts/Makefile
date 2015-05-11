PROGS = \
	conmakehash \
	kallsyms \
	pnmtologo \
	recordmcount

DATA = \
	Kbuild.include \
	Makefile.build \
	Makefile.clean \
	Makefile.extrawarn \
	Makefile.host \
	Makefile.kasan \
	Makefile.lib \
	Makefile.modinst \
	Makefile.modpost \
	mkversion \
	module-common.lds

SCRIPTS =  \
	checkincludes.pl \
	checkstack.pl \
	checkversion.pl \
	depmod.sh \
	gcc-goto.sh \
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
	recordmcount.pl \
	setlocalversion \
	ver_linux

SUBDIRS = \
	basic \
	genksyms \
	kconfig \
	mod

OUTDIR = scripts

include ..//Makefile.inc

CPPFLAGS += -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64
