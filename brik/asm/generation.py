import math
import re
from typing import Self

from brik.asm.platform import Platform
from brik.asm.syntax_tree import *
from brik.datatypes import *
from brik.debug import Debug
from brik.definitions import *
from brik.printer import Printer

class StackFrame:
    def __init__(self, parent: Self | None = None, platform: Platform | None = None):
        self.parent = parent
        if platform is not None:
            self.platform = platform
        elif parent is not None:
            self.platform = parent.platform
        else:
            raise Exception('No platform provided')
        self.contents = {}
        self.offset = 0
    def __getitem__(self, name: str)-> int:
        if name in self.contents:
            return self.contents[name]
        elif self.parent:
            return self.parent[name]
        else:
            raise Exception(f'Ident {name} does not exist')
    def push(self, name: str, val: int | None = None):
        if not val:
            val = self.offset
            self.offset += self.platform.get_word_size()
        if name not in self.contents and self.parent is not None:
            self.parent.push(name, val)
        else:
            self.contents[name] = val
    def contains(self, name: str)-> bool:
        return name in self.contents or (self.parent is not None and self.parent.contains(name))

class AsmGenerator(Debug):
    def __init__(self, platform: Platform, debug: bool = False):
        super().__init__(debug)
        self.platform = platform
        self.known_idents = []
        self.text = Printer('  ')
        self.stack_frame = StackFrame(None, platform)

    def generate_module(self, mod: AsmModule)-> str:
        self.generate_header()

        for (block, _) in mod.text:
            self.generate_block(block)

        return str(mod.data) + '\n' + str(self.text)

    def generate_header(self):
        self.text.append_ln('section .text')
        self.text.append_ln('global _start')
        self.text.append_ln()
        self.text.append_ln('_start:')
        self.text.right()
        self.text.append_ln('call main')
        self.platform.make_exit(self.text, self.platform.ax)
        self.text.append_ln()

    def generate_node(self, node: AsmNode):
        if isinstance(node, AsmBlock): self.generate_block(node)
        elif isinstance(node, AsmCall): self.generate_call(node)
        elif isinstance(node, AsmLiteral): self.generate_asm(node)
        elif isinstance(node, AsmInt): self.generate_int(node)
        elif isinstance(node, AsmString): self.generate_string(node)

    def generate_block(self, body: AsmBlock):
        self.text.left()
        label = self.sanitize_label(body.label)
        self.text.append_ln(f'{label}:')
        self.text.right()
        self.platform.make_stack_frame(self.text)
        self.stack_frame = StackFrame(self.stack_frame)
        for node in body.contents:
            self.generate_node(node)
        self.stack_frame = self.stack_frame.parent
        self.platform.end_stack_frame(self.text)
        self.text.append_ln('ret')

    def generate_call(self, call: AsmCall):
        for op in call.operands:
            self.generate_node(op)
            self.text.append_ln(f'push {self.platform.ax}')
        target = self.sanitize_label(call.target)
        self.text.append_ln(f'call {target}')

    def generate_int(self, num: AsmInt):
        self.text.append_ln(f'mov {self.platform.ax}, {num.value}d')

    def generate_string(self, string: AsmString):
        self.text.append_ln(f'mov {self.platform.ax}, {string.value}')

    _asm_re_register = re.compile(r'%([a-z]{2})')
    _asm_re_reference = re.compile(r'\{([a-z_+\-*^%&|/][0-9a-z_+\-*^%&|/]*)\}')
    def generate_asm(self, node: AsmLiteral):
        self.v_print(f'Generating Asm Node')
        for line in node.asm.split('\n'):
            line = line.strip()
            if len(line) == 0:
                continue
            if matches := AsmGenerator._asm_re_register.finditer(line):
                for match in matches:
                    self.v_print(f'Handling register ref from "{line}"')
                    idnt = match.expand('\\1')
                    self.v_print(f'Matched on {idnt}')
                    reg = self.platform.get_register(idnt)
                    if reg is None:
                        raise Exception(f'Could not get register from name {idnt} in {node.asm}')
                    line = f'{line[:match.start()]}{reg}{line[match.end():]}'
            if matches := AsmGenerator._asm_re_reference.finditer(line):
                for match in matches:
                    offset = self.stack_frame[match.expand('\\1')]
                    sign = '-' if offset < 0 else '+'
                    line = f'{line[:match.start()]}[{self.platform.bp}{sign}{abs(offset)}]{line[match.end():]}'
            print(line)
            self.text.append_ln(line)

    def sanitize_label(self, label: str)-> str:
        return label.replace('+', 'add').replace('-', 'sub').replace('*', 'mul').replace('/', 'div').replace('|', 'pipe').replace('%', 'cent').replace('^', 'caret').replace('&', 'amp')
