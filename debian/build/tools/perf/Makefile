OUTDIR = tools/perf

include ../../Makefile.inc

DEB_HOST_ARCH_CPU := $(shell dpkg-architecture -qDEB_HOST_ARCH_CPU)
NO_LIBUNWIND=1

ifeq ($(DEB_HOST_ARCH_CPU),alpha)
  KERNEL_ARCH_PERF = alpha
else ifeq ($(DEB_HOST_ARCH_CPU),amd64)
  KERNEL_ARCH_PERF = x86_64
  NO_LIBUNWIND=
else ifeq ($(DEB_HOST_ARCH_CPU),arm)
  KERNEL_ARCH_PERF = arm
else ifeq ($(DEB_HOST_ARCH_CPU),hppa)
  KERNEL_ARCH_PERF = parisc
else ifeq ($(DEB_HOST_ARCH_CPU),i386)
  KERNEL_ARCH_PERF = i386
  NO_LIBUNWIND=
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

# disable Gtk UI until it's more usable
MAKE_PERF := $(MAKE) prefix=/usr perfexecdir=share/perf_$(VERSION)-core NO_GTK2=1 NO_PERL=1 V=1 HAVE_CPLUS_DEMANGLE=1 ARCH=$(KERNEL_ARCH_PERF) EXTRA_WARNINGS=-Wno-error NO_LIBUNWIND=$(NO_LIBUNWIND)

all:
ifdef KERNEL_ARCH_PERF
	-mkdir out
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf -f Makefile.perf O=$(CURDIR)/out all VERSION=$(VERSION)
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf/Documentation O=$(CURDIR)/out man VERSION=$(VERSION)
endif

install:
ifdef KERNEL_ARCH_PERF
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf -f Makefile.perf O=$(CURDIR)/out install VERSION=$(VERSION)
# Don't install a 'trace' alias yet:
# - We need a wrapper for it anyway, so there's little point adding a
#   versioned link
# - It doesn't work out-of-the-box as non-root (it depends on debugfs),
#   so it's less widely useful than strace
# - 'perf trace' doesn't take much more typing
	rm -f $(DESTDIR)/usr/bin/trace_$(VERSION)
endif

clean:
	rm -rf out
