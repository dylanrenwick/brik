from brik.asm.syntax_tree import *
from brik.debug import Debug
from brik.definitions import CallDefinition
from brik.patterns import Pattern
from brik.syntax_tree import *

class Transpiler(Debug):
    def __init__(self, debug: bool = False):
        super().__init__(debug)

    def transpile(self, module: Module)-> AsmModule:
        self.asm_mod = AsmModule()
        for define in [d for d in module.defines if isinstance(d, CallDefinition)]:
            self.asm_mod.add_block(self.transpile_define(define), define)
        self.asm_mod.add_block(self.transpile_block('main', module.entry_point), CallDefinition('main', module.entry_point))
        return self.asm_mod

    def transpile_node(self, node: Node)-> AsmNode:
        if isinstance(node, CallNode): return self.transpile_call(node)
        elif isinstance(node, AsmMacroNode): return self.transpile_asm(node)
        else: raise Exception(f'Could not transpile node of type {type(node)}')

    def transpile_define(self, define: CallDefinition)-> AsmBlock:
        return self.transpile_block(define.name, define.body)
    def transpile_block(self, label: str, block: BlockNode)-> AsmBlock:
        return AsmBlock(
            label,
            [self.transpile_node(node) for node in block.contents]
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

    def transpile_asm(self, node: AsmMacroNode)-> AsmLiteral:
        return AsmLiteral(node.asm)

    def check_pattern(self, pattern: Pattern, operands: list[AsmExpr])-> bool:
        if len(pattern.args) != len(operands): return False
        for i in range(0, len(operands)):
            if pattern.args[i][1] != operands[i].datatype:
                return False
        return True