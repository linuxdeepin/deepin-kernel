include $(top_rulesdir)/Makefile.inc

ifneq (,$(findstring nostrip,$(DEB_BUILD_OPTIONS)))
	DEBUG = true
endif

all:
	$(shell dpkg-buildflags --export=cmdline) $(MAKE) -C $(top_srcdir)/tools/power/cpupower O=$(CURDIR) DEBUG=$(DEBUG) CPUFREQ_BENCH=false V=true

install:
	$(MAKE) -C $(top_srcdir)/tools/power/cpupower O=$(CURDIR) install mandir=/usr/share/man DESTDIR=$(DESTDIR) CPUFREQ_BENCH=false
ifneq (,$(filter nodoc,$(DEB_BUILD_PROFILES)))
	rm -rf $(DESTDIR)/usr/share/man
endif

clean:
	$(MAKE) -C $(top_srcdir)/tools/power/cpupower O=$(CURDIR) clean
