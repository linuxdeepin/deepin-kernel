OUTDIR = tools/perf

include ../../Makefile.inc

DEB_HOST_ARCH_CPU := $(shell dpkg-architecture -qDEB_HOST_ARCH_CPU)

ifeq ($(DEB_HOST_ARCH_CPU),alpha)
  KERNEL_ARCH_PERF = alpha
else ifeq ($(DEB_HOST_ARCH_CPU),amd64)
  KERNEL_ARCH_PERF = x86_64
else ifeq ($(DEB_HOST_ARCH_CPU),arm)
  KERNEL_ARCH_PERF = arm
else ifeq ($(DEB_HOST_ARCH_CPU),arm64)
  KERNEL_ARCH_PERF = arm64
else ifeq ($(DEB_HOST_ARCH_CPU),hppa)
  KERNEL_ARCH_PERF = parisc
else ifeq ($(DEB_HOST_ARCH_CPU),i386)
  KERNEL_ARCH_PERF = i386
else ifeq ($(DEB_HOST_ARCH_CPU),mips)
  KERNEL_ARCH_PERF = mips
else ifeq ($(DEB_HOST_ARCH_CPU),mips64)
  KERNEL_ARCH_PERF = mips
else ifeq ($(DEB_HOST_ARCH_CPU),mips64el)
  KERNEL_ARCH_PERF = mips
else ifeq ($(DEB_HOST_ARCH_CPU),mipsel)
  KERNEL_ARCH_PERF = mips
else ifeq ($(DEB_HOST_ARCH_CPU),powerpc)
  KERNEL_ARCH_PERF = powerpc
else ifeq ($(DEB_HOST_ARCH_CPU),powerpc64)
  KERNEL_ARCH_PERF = powerpc
else ifeq ($(DEB_HOST_ARCH_CPU),ppc64el)
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

MAKE_PERF := $(MAKE) prefix=/usr V=1 ARCH=$(KERNEL_ARCH_PERF) EXTRA_WARNINGS=-Wno-error

# Disable Gtk UI until it's more usable
MAKE_PERF += NO_GTK2=1

# Include version in all directory names
MAKE_PERF += perfexecdir=share/perf_$(VERSION)-core plugindir=/usr/lib/traceevent_$(VERSION)/plugins

# perf can link against libbfd if available, but the result is
# undistributable as they are licenced under GPL v2 and v3+
# respectively.  Override detection of libbfd and insist that
# cplus_demangle() can be found in libiberty (LGPL v2.1+).
MAKE_PERF += feature-libbfd=0 HAVE_CPLUS_DEMANGLE_SUPPORT=1

all:
ifdef KERNEL_ARCH_PERF
	-mkdir out
# perf changes some default directories depending on whether DESTDIR is
# set.  We must define it even when building to avoid a rebuild when we
# run 'make install'.
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf -f Makefile.perf O=$(CURDIR)/out all VERSION=$(VERSION) DESTDIR=dummy
	+$(MAKE_PERF) -C $(top_srcdir)/tools/perf/Documentation O=$(CURDIR)/out man VERSION=$(VERSION)
# Check that perf didn't get linked against libbfd
	type ldd
	! ldd $(CURDIR)/out/perf | grep '\blibbfd'
# Check that it includes cplus_demangle from libiberty
	grep cplus_demangle $(CURDIR)/out/perf
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
