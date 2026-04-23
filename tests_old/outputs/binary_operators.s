	.globl _main
_main:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$24, %rsp
	movl	$6, %eax
	cdq
	movl	$4, %r10d
	idivl	%r10d
	movl	%edx, -4(%rbp)
	movl	-4(%rbp), %r10d
	movl	%r10d, -8(%rbp)
	movl	-8(%rbp), %r11d
	imull	$3, %r11d
	movl	%r11d, -8(%rbp)
	movl	$10, -12(%rbp)
	movl	-8(%rbp), %r10d
	subl	%r10d, -12(%rbp)
	movl	$8, %eax
	cdq
	movl	$2, %r10d
	idivl	%r10d
	movl	%eax, -16(%rbp)
	movl	-12(%rbp), %r10d
	movl	%r10d, -20(%rbp)
	movl	-16(%rbp), %r10d
	addl	%r10d, -20(%rbp)
	movl	-20(%rbp), %eax
	cdq
	movl	$5, %r10d
	idivl	%r10d
	movl	%edx, -24(%rbp)
	movl	-24(%rbp), %eax
	movq	%rbp, %rsp
	popq	%rbp
	ret
