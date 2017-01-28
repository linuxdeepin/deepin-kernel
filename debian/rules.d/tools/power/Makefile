SUBDIRS = \
	cpupower

ifneq ($(filter i386 amd64 x32,$(DEB_HOST_ARCH)),)
SUBDIRS += x86
endif

include $(top_rulesdir)/Makefile.inc
