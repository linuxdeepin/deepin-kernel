PROGS = \
	hv_fcopy_daemon \
	hv_kvp_daemon \
	hv_vss_daemon

OUTDIR = tools/hv
prefix = /usr/sbin

include ../../Makefile.inc

install-local-progs: $(PROGS)
	@for p in $^; do \
	  echo " install -m755 '$$p' '$(DESTDIR)/$(prefix)'"; \
	  install -D -m755 "$$p" "$(DESTDIR)/$(prefix)/$$(basename $$p)"; \
	done
