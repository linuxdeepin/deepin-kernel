ifeq ($(filter i386 amd64 x32,$(DEB_BUILD_ARCH)),)

# Build nothing
include $(top_rulesdir)/Makefile.inc

else

PROGS = \
	hv_fcopy_daemon \
	hv_kvp_daemon \
	hv_vss_daemon \
	check-hyperv

prefix = /usr/sbin

include $(top_rulesdir)/Makefile.inc

install-local-progs: $(PROGS)
	@for p in $(filter-out check-hyperv,$^); do \
	  echo " install -m755 '$$p' '$(DESTDIR)/$(prefix)'"; \
	  install -D -m755 "$$p" "$(DESTDIR)/$(prefix)/$$(basename $$p)"; \
	done
	install -D -m755 check-hyperv '$(DESTDIR)/lib/hyperv-daemons/check-hyperv'

endif
