#
# Variables 
#
include_common_config := no
headers_extra := arch/x86_64/kernel/ams-offsets.s
initrd_modules := kernel/drivers/video/vesafb.ko kernel/security/capability.ko
headers_dirs = x86_64
build_makeflags := 'V=1 CC=gcc-3.4'
default_config := default

