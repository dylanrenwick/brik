import math
import re
from typing import Self

from brik.asm.platform import Platform
from brik.datatypes import *
from brik.debug import Debug
from brik.definitions import *
from brik.printer import Printer
from brik.syntax_tree import *

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
        self.data = DataSection()
        self.stack_frame = StackFrame(None, platform)

    def generate_module(self, mod: Module)-> str:
        self.generate_header()

        for define in mod.defines:
            self.generate_definition(define)
        self.text.append_ln()

        self.generate_routine('main', mod.entry_point)
        return str(self.data) + '\n' + str(self.text)

    def generate_header(self):
        self.text.append_ln('section .text')
        self.text.append_ln('global _start')
        self.text.append_ln()
        self.text.append_ln('_start:')
        self.text.right()
        self.text.append_ln('call main')
        self.platform.make_exit(self.text, self.platform.ax)
        self.text.append_ln()

    def generate_node(self, node: Node):
        if isinstance(node, BlockNode): self.generate_block(node)
        elif isinstance(node, CallNode): self.generate_call(node)
        elif isinstance(node, NumberNode): self.generate_number(node)
        elif isinstance(node, StringNode): self.generate_string(node)
        elif isinstance(node, AsmMacroNode): self.generate_asm(node)

    def generate_block(self, block: BlockNode, pattern: Pattern | None = None):
        self.stack_frame = StackFrame(self.stack_frame)
        if pattern:
            self.v_print(f'Pattern has {len(pattern.args)}')
            for i in range(0, len(pattern.args)):
                arg = pattern.args[i]
                self.stack_frame.push(arg[0], self.platform.get_word_size() * -1 * (i + 2))
        for node in block.contents:
            self.generate_node(node)
        self.stack_frame = self.stack_frame.parent

    def generate_definition(self, definition: Definition):
        if isinstance(definition, VarDefinition): self.generate_var_definition(definition)
        elif isinstance(definition, CallDefinition): self.generate_call_definition(definition)

    def generate_var_definition(self, definition: VarDefinition):
        if definition.value:
            self.generate_node(definition.value)
        self.text.append_ln(f'push {self.platform.ax} ; assigment of {definition.name}')
        self.stack_frame.push(definition.name)
        
    def generate_call_definition(self, definition: CallDefinition):
        self.generate_routine(definition.name, definition.body, definition.pattern)

    def generate_routine(self, name: str, body: BlockNode, pattern: Pattern | None = None):
        self.text.left()
        self.text.append_ln(f'{name}:')
        self.text.right()
        self.platform.make_stack_frame(self.text)
        self.generate_block(body, pattern)
        self.platform.end_stack_frame(self.text)
        self.text.append_ln('ret')

    def generate_call(self, call: CallNode):
        for op in call.operands:
            self.generate_node(op)
            self.text.append_ln(f'push {self.platform.ax}')
        self.text.append_ln(f'call {call.name}')

    def generate_number(self, num: NumberNode):
        self.text.append_ln(f'mov {self.platform.ax}, {num.value}d')

    def generate_string(self, string: StringNode):
        name = self.data.add_autoname(string.value)
        self.text.append_ln(f'mov {self.platform.ax}, {name}')

    _asm_re_register = re.compile(r'%([a-z]{2})')
    _asm_re_reference = re.compile(r'\{([a-z_+\-*^%&|/][0-9a-z_+\-*^%&|/]*)\}')
    def generate_asm(self, node: AsmMacroNode):
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
            self.text.append_ln(line)

