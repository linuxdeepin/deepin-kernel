include $(top_rulesdir)/Makefile.inc

all:
# For now, only supported target architecture is x86.  Later we'll need to build
# for multiple targets and add a wrapper, same as for modpost.
	$(MAKE) -C $(top_srcdir)/tools/objtool O=$(CURDIR) ARCH=x86

install:
	install -D -m755 objtool $(DESTDIR)/$(installdir)/objtool
