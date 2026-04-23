	.globl _main
_main:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movl	$42, -4(%rbp)
	andl	$15, -4(%rbp)
	movl	$7, -8(%rbp)
	xorl	$3, -8(%rbp)
	movl	-4(%rbp), %r10d
	movl	%r10d, -12(%rbp)
	movl	-8(%rbp), %r10d
	orl		%r10d, -12(%rbp)
	movl	-12(%rbp), %r10d
	movl	%r10d, -16(%rbp)
	sall	$2, -16(%rbp)
	movl	-16(%rbp), %r10d
	movl	%r10d, -20(%rbp)
	sarl	$1, -20(%rbp)
	movl	-20(%rbp), %eax
	movq	%rbp, %rsp
	popq	%rbp
	ret
