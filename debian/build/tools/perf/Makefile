OUTDIR = tools/perf

include ../../Makefile.inc

DEB_HOST_ARCH_CPU := $(shell dpkg-architecture -qDEB_HOST_ARCH_CPU)

ifeq ($(DEB_HOST_ARCH_CPU),amd64)
  KERNEL_ARCH_PERF = x86
else ifeq ($(DEB_HOST_ARCH_CPU),arm)
  KERNEL_ARCH_PERF = arm
else ifeq ($(DEB_HOST_ARCH_CPU),i386)
  KERNEL_ARCH_PERF = x86
else ifeq ($(DEB_HOST_ARCH_CPU),powerpc)
  KERNEL_ARCH_PERF = powerpc
else ifeq ($(DEB_HOST_ARCH_CPU),powerpc64)
  KERNEL_ARCH_PERF = powerpc
else ifeq ($(DEB_HOST_ARCH_CPU),s390)
  KERNEL_ARCH_PERF = s390
else ifeq ($(DEB_HOST_ARCH_CPU),s390x)
  KERNEL_ARCH_PERF = s390
else ifeq ($(DEB_HOST_ARCH_CPU),sh4)
  KERNEL_ARCH_PERF = sh
else ifeq ($(DEB_HOST_ARCH_CPU),sparc)
  KERNEL_ARCH_PERF = sparc
else ifeq ($(DEB_HOST_ARCH_CPU),sparc64)
  KERNEL_ARCH_PERF = sparc
endif

MAKE_PERF := $(MAKE) prefix=/usr perfexecdir=share/perf_$(VERSION)-core NO_PERL=1 V=2 HAVE_CPLUS_DEMANGLE=1 ARCH=$(KERNEL_ARCH_PERF) EXTRA_WARNINGS=-Wno-error

all:
ifdef KERNEL_ARCH_PERF
	-mkdir out
	# upstream makefile is broken
	cp -al $(top_srcdir)/tools/perf/Documentation doc
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf O=$(CURDIR)/out all VERSION=$(VERSION)
	+$(MAKE_PERF) -C doc man VERSION=$(VERSION)
endif

install:
ifdef KERNEL_ARCH_PERF
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf O=$(CURDIR)/out install VERSION=$(VERSION)
	+$(MAKE_PERF) -C doc install-man VERSION=$(VERSION)
endif

clean:
	rm -rf doc out
