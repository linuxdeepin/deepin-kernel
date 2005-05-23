#
# This Makefile executes the unpack/build/binary targets for a single
# subarch, which is passed in the subarch variable. Empty subarch
# variable means that we are building for an arch without the subarch.
# Additionally, variables version, abiname and ktver are
# expected to be available (need to be exported from the parent process).
# It is possible to override the flavours by setting the flavours
# variable. 
#
SHELL  := sh -e
debver := $(version)-$(abiname)
uver   := $(subst .,_,$(version))
debnum := -$(abiname)
kbpkg  := kernel-kbuild-$(version)-$(abiname)
# This will eventually have to be changed to a command, applying
# the debian's patches from the local tree (arch/patches?)
kpatch := /usr/src/kernel-patches/all/$(version)/apply/debian $(version)-$(ktver)
DEBIAN_UPSTREAM_VERSION := $(version)
ifeq (,$(DEB_HOST_ARCH))
  DEB_HOST_ARCH  := $(shell dpkg-architecture -qDEB_HOST_ARCH)
  DEB_BUILD_ARCH := $(shell dpkg-architecture -qDEB_BUILD_ARCH)
endif
export version debnum DEBIAN_UPSTREAM_VERSION

karch := $(DEB_HOST_ARCH)
#
# Build the list of common config files to be included
#
ifeq ($(subarch),none)
  basedir := arch/$(karch)
  append  := 
else
  basedir := arch/$(karch)/$(subarch)
  append  := -$(subarch)
endif
default := $(basedir)/config.default
configs := $(notdir $(wildcard $(basedir)/config.*))
configs := $(filter-out config.common config.default, $(configs))
tkdir   := kernel-source-$(version)
kdir    := kernel-source-$(version)-$(subarch)
ifndef flavours
  flavours := $(patsubst config.%,%,$(configs))
endif

-include $(basedir)/Makefile.inc

#
# Here we construct the command lines for different make-kpkg
# calls (build, kernel-image, kernel-headers) based on the values
# of variables defined so far and provided by the arch/subarch
# in Makefile.inc. @flavour@ in the expressions is going to be
# replaced by the flavour for which the command is run. 
#
kpkg_headers_cmd := HEADER_CLEAN_HOOK='$(CURDIR)/header-install-$(subarch)'
kpkg_headers_cmd += make-kpkg --append-to-version $(debnum)$(append)
kpkg_build_cmd  := make-kpkg --append-to-version $(debnum)-@flavour@
ifdef added_patches
  kpkg_headers_cmd += --added_patches $(subst @uver@,$(uver),$(added_patches))
  kpkg_build_cmd   += --added_patches $(subst @uver@,$(uver),$(added_patches))
endif
ifdef build_subarch
  kpkg_build_cmd += --subarch $(build_subarch)
endif
ifdef headers_subarch
  kpkg_headers_cmd += --subarch $(headers_subarch)
endif
ifdef build_makeflags
  kpkg_build_cmd := MAKEFLAGS=$(build_makeflags) $(kpkg_build_cmd)
endif
#
# Note that next variable (kpkg_image_pre) is not going to be evaluated
# immediately. When referenced, the variable $* will have the current
# flavour for which the command is executed. So if this flavour will
# happen to be in the image_prefix_flavours list, the call to make-kpkg
# will be prepended with contents if image_prefix.
#
kpkg_image_pre = $(if $(filter $*,$(image_prefix_flavours)),$(image_prefix))
kpkg_image_cmd := $(kpkg_build_cmd) --initrd kernel_image
kpkg_build_cmd += build
kpkg_headers_cmd += kernel-headers
ifndef headers_dirs
  headers_dirs = $(karch)
endif
ifneq (no,$(include_common_config))
  ccommon := arch/config.common
endif
ccommon += arch/$(karch)/config.common arch/$(karch)/$(subarch)/config.common
#
# Here we build lists of directories and stamps which we will depend on.
# For each class of such targets there is a pattern rule which will catch
# it and do the right thing.
#
bdirs   := $(addprefix build-$(subarch)-, $(flavours))
bstamps := $(addprefix build-stamp-$(subarch)-, $(flavours))
istamps := $(addprefix install-stamp-$(subarch)-, $(flavours))
#
# Targets
#
unpack: unpack-stamp-$(subarch)
unpack-stamp-$(subarch): $(configs) header-install-$(subarch) $(bdirs)
	touch unpack-stamp-$(subarch)

build: build-stamp-$(subarch)
build-stamp-$(subarch): unpack-stamp-$(subarch) $(bstamps)
	touch build-stamp-$(subarch)

binary-indep: build
binary-arch: build headers-stamp $(istamps)
	mv *.deb ..

install-stamp-$(subarch)-%: build-$(subarch)-% build-stamp-$(subarch)-%
	cp -al $< install-$*;
	cd install-$*; \
	$(strip $(kpkg_image_pre) $(subst @flavour@,$*,$(kpkg_image_cmd)))
	cat install-$*/debian/files >> debian/files;
	rm -rf install-$*;
	touch install-stamp-$(subarch)-$*

headers-stamp: $(kdir)
	dh_testdir
	dh_clean -k
	dh_installdirs
	cp $(default) $(kdir)/.config
	cd $(kdir); $(kpkg_headers_cmd)
	cat $(kdir)/debian/files >> debian/files
	touch headers-stamp

binary:	binary-indep binary-arch

header-install-$(subarch): header-install.in
	sed -e 's,@kbpkg@,$(kbpkg),g'				\
	    -e 's,@ksource_dir@,$(CURDIR)/$(kdir),g'		\
	    -e 's,@headers_dirs@,$(headers_dirs),g'		\
	    -e 's,@headers_extra@,$(headers_extra),g'		\
            header-install.in > header-install-$(subarch)
	chmod u+x header-install-$(subarch)
#
# The way to make the correct package names is to make a
# subarch-specific post-install script...
#
post-install-$(subarch): post-install.in
	sed -e 's,@initrd_modules@,$(initrd_modules),'	\
	    -e 's,@append_subarch@,$(append),'		\
	    post-install.in > post-install-$(subarch)
#
# Generates the kernel config file for a subarch by merging
# the arch-independent config file (arch/config.common),
# arch-specific config file (arch/$(karch)/config.common),
# and subarch specific one (arch/$(karch)/config.subarch).
# It is possible to avoid the inclusion of the arch-indep
# config file by setting include_common_config = no in the
# arch/$(karch)/Makefile.inc.
#
config.%:
	@echo "configs=$(configs)"
	@echo "Generating configuration file $@:"
	rm -f $@
	for i in $(ccommon); do	\
	  if [ -f $${i} ]; then	\
	    cat $${i} >> $@;	\
	  fi;			\
	done
#	Flavour config file must be present
	cat $(basedir)/$@ >> $@			 

$(kdir): post-install-$(subarch)
	dh_testdir
	tar jxf /usr/src/$(tkdir).tar.bz2
	mkdir -p $(tkdir)/debian
	cp debian/changelog $(tkdir)/debian
	cp debian/control   $(tkdir)/debian
	cp debian/copyright $(tkdir)/debian
	touch $(tkdir)/debian/official
	install post-install-$(subarch) $(tkdir)/debian/post-install
	cd $(tkdir) && $(kpatch)
#	Arch/subarch-specific patches
	if [ -d $(basedir)/patches ] &&				\
	   [ -s $(basedir)/patches/list ]; then			\
	  cd $(tkdir);						\
	  for i in $$(cat ../$(basedir)/patches/list); do	\
	    patch -p1 < ../$(basedir)/patches/$${i};		\
	  done;							\
	fi
	mv $(tkdir) $@
#
# This target performs a build for a particular flavour. Note
# that in this file it should be always placed *before* the
# build-$(subarch)-% target, which creates the build directory.
#
# Some arches have extra arch/${ARCH}/kernel/asm-offsets.s files
# which have to be included in kernel-headers. The problem is that
# they are only generated during build and we never performed a
# full build in the directory $(kdir) where kernel-headers are
# built. So, after build we check whether current build arch has
# such a file and symlink it into the $(kdir) if necessary.
# Note that to get into the kernel-headers package the arch/subarch
# still needs variables headers_dirs and headers_extra set.
#
build-stamp-$(subarch)-%: build-$(subarch)-%
	dh_testdir
	PATH=$$PWD/bin:$$PATH;					\
	cd $<;							\
	$(subst @flavour@,$*,$(kpkg_build_cmd));		\
	$(if $(image_postproc),$(image_postproc),true);		\
	arch=$$(basename $$(readlink include/asm));		\
	arch="${arch#asm-}";					\
	src="arch/$${arch}/kernel/asm-offsets.s";		\
	dst="../$(kdir)/$${src}";				\
	if [ -f "$${src}" ] && [ ! -L "$${dst}" ]; then		\
	  ln -s "$${src}" "$${dst}";				\
	fi	
	touch build-stamp-$(subarch)-$*
#
# Creates a build directory for a particular flavour
#
build-$(subarch)-%: $(kdir) config.%
	dh_testdir
	if [ ! -d $@ ]; then					\
	  cp -al $(kdir) $@;					\
	  cp config.$* $@/.config;				\
	fi

.PHONY: build unpack binary-indep binary-arch binary
