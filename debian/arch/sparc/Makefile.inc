#
# Variables 
#
image_postproc = strip -R .comment -R .note -K sun4u_init -K _end -K _start arch/$(subst 32,,$(subst -smp,,$*))/boot/image
