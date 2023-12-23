import math
import re
from typing import Self

from brik.asm.platform import Platform
from brik.asm.syntax_tree import *
from brik.datatypes import *
from brik.debug import Debug
from brik.definitions import *
from brik.printer import Printer

class AsmGenerator(Debug):
    def __init__(self, platform: Platform, debug: bool = False):
        super().__init__(debug)
        self.platform = platform
        self.known_idents = []
        self.text = Printer('  ')

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
        for node in body.contents:
            self.generate_node(node)
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

    def generate_asm(self, node: AsmLiteral):
        self.text.append_ln(node.asm)

    def sanitize_label(self, label: str)-> str:
        return label.replace('+', 'add').replace('-', 'sub').replace('*', 'mul').replace('/', 'div').replace('|', 'pipe').replace('%', 'cent').replace('^', 'caret').replace('&', 'amp')
