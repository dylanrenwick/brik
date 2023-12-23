import re

from brik.asm.platform import Platform
from brik.asm.syntax_tree import *
from brik.debug import Debug
from brik.definitions import CallDefinition
from brik.patterns import Pattern
from brik.syntax_tree import *

class StackFrame:
    def __init__(self, parent: Self | None = None):
        self.parent = parent
        self.contents = {}
        self.offset = 2
    def __getitem__(self, name: str)-> int:
        if name in self.contents:
            return self.contents[name]
        elif self.parent:
            return self.parent[name]
        else:
            raise Exception(f'Ident {name} does not exist')
    def push(self, name: str, val: int | None = None):
        if val is None:
            val = self.offset
            self.offset += 1
        if name not in self.contents and self.parent is not None and self.parent.contains(name):
            self.parent.push(name, val)
        else:
            self.contents[name] = val
    def push_pattern(self, pattern: Pattern):
        for (name, _) in pattern.args:
            self.push(name)

    def contains(self, name: str)-> bool:
        return name in self.contents or (self.parent is not None and self.parent.contains(name))

class Transpiler(Debug):
    def __init__(self, platform: Platform, debug: bool = False):
        super().__init__(debug)
        self.platform = platform
        self.stack_frame = StackFrame(None)

    def transpile(self, module: Module)-> AsmModule:
        self.asm_mod = AsmModule()
        for define in [d for d in module.defines if isinstance(d, CallDefinition)]:
            self.asm_mod.add_block(self.transpile_define(define), define)
        define = CallDefinition('main', module.entry_point)
        self.asm_mod.add_block(self.transpile_define(define), define)
        return self.asm_mod

    def transpile_node(self, node: Node)-> AsmNode | None:
        if isinstance(node, CallNode): return self.transpile_call(node)
        elif isinstance(node, AsmMacroNode): return self.transpile_asm(node)
        elif isinstance(node, NumberNode): return self.transpile_number(node)
        elif isinstance(node, StringNode): return self.transpile_string(node)
        elif isinstance(node, ReferenceNode): return None
        else: raise Exception(f'Could not transpile node of type {type(node)}')

    def transpile_define(self, define: CallDefinition)-> AsmBlock:
        self.stack_frame = StackFrame(self.stack_frame)
        self.stack_frame.push_pattern(define.pattern)
        nodes = [self.transpile_node(node) for node in define.body.contents]
        if self.stack_frame.parent is not None:
            self.stack_frame = self.stack_frame.parent
        return AsmBlock(
            define.name,
            [node for node in nodes if node is not None]
        )

    def transpile_expr(self, node: Node)-> AsmExpr:
        if isinstance(node, CallNode): return self.transpile_call(node)
        elif isinstance(node, NumberNode): return self.transpile_number(node)
        elif isinstance(node, StringNode): return self.transpile_string(node)
        else: raise Exception('Could not transpile expression')
    def transpile_number(self, node: NumberNode)-> AsmInt:
        return AsmInt(node.value)
    def transpile_string(self, node: StringNode)-> AsmString:
        name = self.asm_mod.data.add_autoname(node.value)
        return AsmString(name)
    def transpile_call(self, node: CallNode)-> AsmCall:
        target = self.asm_mod.get_block(node.name)
        if not target:
            raise Exception(f'Callable with name {node.name} not found')
        exprs = []
        if len(node.operands):
            exprs = [self.transpile_expr(op) for op in node.operands]
            if not self.check_pattern(target[1].pattern, exprs):
                raise Exception(f'Callable with name {node.name} does not match operands provided')
        return AsmCall(node.name, target[0].data_type(), exprs)

    _asm_re_register = re.compile(r'%([a-z]{2})')
    _asm_re_reference = re.compile(r'\{([a-z_+\-*^%&|/][0-9a-z_+\-*^%&|/]*)\}')
    def transpile_asm(self, node: AsmMacroNode)-> AsmLiteral:
        self.v_print(f'Generating Asm Node')
        asm = ''
        for line in node.asm.split('\n'):
            line = line.strip()
            if len(line) == 0:
                continue
            if matches := Transpiler._asm_re_register.finditer(line):
                for match in matches:
                    self.v_print(f'Handling register ref from "{line}"')
                    idnt = match.expand('\\1')
                    self.v_print(f'Matched on {idnt}')
                    reg = self.platform.register(idnt)
                    if reg is None:
                        raise Exception(f'Could not get register from name {idnt} in {node.asm}')
                    line = f'{line[:match.start()]}{reg}{line[match.end():]}'
            if matches := Transpiler._asm_re_reference.finditer(line):
                for match in matches:
                    offset = self.stack_frame[match.expand('\\1')] * self.platform.word_size()
                    sign = '-' if offset < 0 else '+'
                    line = f'{line[:match.start()]}[{self.platform.bp}{sign}{abs(offset)}]{line[match.end():]}'
            if len(asm) > 0: asm += '\n'
            asm += line
        return AsmLiteral(asm)

    def check_pattern(self, pattern: Pattern, operands: list[AsmExpr])-> bool:
        if len(pattern.args) != len(operands): return False
        for i in range(0, len(operands)):
            if pattern.args[i][1] != operands[i].datatype:
                return False
        return True