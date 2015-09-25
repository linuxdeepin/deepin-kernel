OUTDIR = tools/lib/lockdep

include ../../../Makefile.inc

DEB_HOST_MULTIARCH := $(shell dpkg-architecture -qDEB_HOST_MULTIARCH)

MAKE_LOCKDEP := $(MAKE) -C $(top_srcdir)/$(OUTDIR) O=$(CURDIR)/out V=1 \
	prefix=/usr libdir_relative=lib/$(DEB_HOST_MULTIARCH) \
	LIBLOCKDEP_VERSION=$(VERSION) \
	CONFIG_FLAGS='$(CFLAGS) $(filter -D%,$(CPPFLAGS))' LDFLAGS='$(LDFLAGS)'

unexport CFLAGS

all:
	mkdir -p out
	$(MAKE_LOCKDEP)

install:
	$(MAKE_LOCKDEP) install
	mkdir -p $(DESTDIR)/usr/include
	cp -R $(top_srcdir)/$(OUTDIR)/include/liblockdep $(DESTDIR)/usr/include/
	ln -s liblockdep.so.$(VERSION) \
		$(DESTDIR)/usr/lib/$(DEB_HOST_MULTIARCH)/liblockdep.so
# Upstream lockdep preload script is not suitable for installation
	sed 's/@VERSION@/$(VERSION)/' lockdep.in > $(DESTDIR)/usr/bin/lockdep
	chmod 755 $(DESTDIR)/usr/bin/lockdep

clean:
	rm -rf out
