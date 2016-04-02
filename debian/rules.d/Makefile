DATA = \
	Kbuild \
	Makefile \

SUBDIRS = \
	scripts \
	tools

include $(top_rulesdir)/Makefile.inc

# Build userland headers first
unexport VERSION
all-local:
	$(MAKE) -C $(top_srcdir) O=$(CURDIR) \
		INSTALL_HDR_PATH=$(CURDIR) headers_install
all-recursive: all-local
