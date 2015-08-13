DATA = \
	Kbuild \
	Makefile \

SUBDIRS = \
	scripts \
	tools

OUTDIR = .

include Makefile.inc

# Build userland headers first
unexport VERSION
all-local:
	$(MAKE) -C $(top_srcdir) O=$(CURDIR)/out \
		INSTALL_HDR_PATH=$(CURDIR) headers_install
all-recursive: all-local

clean-local::
	rm -rf generated include out
