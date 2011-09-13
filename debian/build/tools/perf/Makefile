OUTDIR = tools/perf

include ../../Makefile.inc

all:
	-mkdir out
	make -C $(top_srcdir)/tools/perf O=$(CURDIR)/out

clean:
	rm -rf out
