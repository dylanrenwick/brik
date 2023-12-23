from unittest import TestCase
from brik import Brik
from brik.asm_platform import CompilerPlatform

class TestCompile(TestCase):
    def test_compile(self):
        compiler = Brik(CompilerPlatform.LINUX_X86_64)
        asm = compiler.compile('''
        [print 123]
        ''')
        self.assertEqual(
            asm,
            '''section .text
global _start

_start:
  call main
  mov rdi, rax
  mov rax, 60d
  syscall


main:
  push rbp
  mov rbp, rsp
  call print
  mov rsp, rbp
  pop rbp
  ret
'''
        )

    def test_asm(self):
        compiler = Brik(CompilerPlatform.LINUX_X86_64)
        source = '''
        [#def putchar <c> [(
            [#asm "
                mov %si, %bp
                mov %cx, {c}
                add %si, %cx
                mov %ax, 1
                mov %di, 1
                mov %dx, 1
                syscall
            "]
        )]]
        '''
        asm = compiler.compile(source)
        self.assertEqual(
            asm,
            '''section .text
global _start

_start:
  call main
  mov rdi, rax
  mov rax, 60d
  syscall

putchar:
  push rbp
  mov rbp, rsp
  mov rsi, rbp
  mov rcx, [rbp-16]
  add rsi, rcx
  mov rax, 1
  mov rdi, 1
  mov rdx, 1
  syscall
  mov rsp, rbp
  pop rbp
  ret

main:
  push rbp
  mov rbp, rsp
  mov rsp, rbp
  pop rbp
  ret
'''
        )

    def test_simple(self):
        compiler = Brik(CompilerPlatform.LINUX_X86_64)
        source = '123'
        asm = compiler.compile(source)
        self.assertEqual(
            asm,
            '''section .text
global _start

_start:
  call main
  mov rdi, rax
  mov rax, 60d
  syscall


main:
  push rbp
  mov rbp, rsp
  mov rax, 123d
  mov rsp, rbp
  pop rbp
  ret
'''
        )
