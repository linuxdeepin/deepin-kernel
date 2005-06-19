#
# Variables 
#
include_common_config := no
headers_dirs := sparc | sparc64
headers_subarch := sparc64
build_subarch := @flavour@
image_postproc = strip -R .comment -R .note -K sun4u_init -K _end -K _start arch/$(subst 32,,$(subst -smp,,$*))/boot/image
image_prefix_flavours := sparc32 sparc32-smp
image_prefix := sparc32

