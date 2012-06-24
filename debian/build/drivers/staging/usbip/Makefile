srcdir := $(top_srcdir)/drivers/staging/usbip/userspace

# Make sure we don't override top_srcdir in the sub-make.  'unexport
# top_srcdir' is *not* sufficient; nor is adding 'MAKEFLAGS=' to the
# sub-make command line.
unexport MAKEFLAGS

all:
	cd $(srcdir) && ./autogen.sh
	mkdir -p userspace
	cd userspace && $(srcdir)/configure \
		--prefix=/usr \
		--with-tcp-wrappers \
		--with-usbids-dir=/usr/share/misc \
		--disable-shared
	$(MAKE) -C userspace

install:
	$(MAKE) -C userspace install

clean:
	rm -rf $(addprefix $(srcdir)/,autom4te.cache aclocal.m4 config.guess config.h.in config.sub configure depcomp install-sh ltmain.sh missing)
	find $(srcdir)/ -name Makefile.in -delete
	rm -rf userspace
