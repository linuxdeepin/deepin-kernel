OUTDIR = tools/power/cpupower
prefix = /usr/sbin

include ../../../Makefile.inc

ifneq (,$(findstring nostrip,$(DEB_BUILD_OPTIONS)))
	DEBUG = true
endif

all:
	mkdir out
	$(shell dpkg-buildflags --export=cmdline) $(MAKE) -C $(top_srcdir)/tools/power/cpupower -f Makefile O=$(CURDIR)/out DEBUG=$(DEBUG) CPUFREQ_BENCH=false V=true

install:
	$(MAKE) -C $(top_srcdir)/tools/power/cpupower -f Makefile O=$(CURDIR)/out install mandir=/usr/share/man DESTDIR=$(DESTDIR) CPUFREQ_BENCH=false

clean:
	mkdir -p out
	$(MAKE) -C $(top_srcdir)/tools/power/cpupower -f Makefile O=$(CURDIR)/out clean
	rm -rf out
