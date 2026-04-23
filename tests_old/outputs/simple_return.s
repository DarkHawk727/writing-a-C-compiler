.globl _main
_main:
	pushq 	%rbp
	movq	%rsp, %rbp
	movl	$69, %eax
	popq	%rbp
	retq
