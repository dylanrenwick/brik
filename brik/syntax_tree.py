from abc import ABC, abstractmethod
from typing import Self

from brik.datatypes import *
from brik.printer import Printer

class Node(ABC):
    @abstractmethod
    def __pretty_print__(self, printer: Printer):
        pass
    @abstractmethod
    def data_type(self)-> DataType:
        return DataType.UNKNOWN
    def __eq__(self, other: Self):
        p_a = Printer('')
        p_a.print(self)
        p_b = Printer('')
        p_b.print(other)
        return str(p_a) == str(p_b)

class CallNode(Node):
    def __init__(self, name: str, operands: list[Node] = []):
        self.name = name
        self.operands = operands
    def __pretty_print__(self, printer: Printer):
        printer.append(f'Call {self.name} [')
        if self.operands:
            printer.append_ln()
            printer.right()
            for op in self.operands:
                printer.print(op)
            printer.left()
        printer.append_ln(']')
    def data_type(self)-> DataType:
        return super().data_type()

class AsmMacroNode(Node):
    def __init__(self, asm: str):
        self.asm = asm
    def __pretty_print__(self, printer: Printer):
        printer.append_ln(f'#asm [')
        printer.right()
        printer.append_ln(self.asm)
        printer.left()
        printer.append_ln(']')
    def data_type(self)-> DataType:
        return DataType.VOID

class ListNode(Node):
    def __init__(self, contents: list[Node] = []):
        self.contents = contents
    def __pretty_print__(self, printer: Printer):
        printer.append_ln('List (')
        printer.right()
        for node in self.contents:
            printer.print(node)
        printer.left()
        printer.append_ln(')')
    def data_type(self)-> DataType:
        inner_type: DataType = self.contents[-1].data_type() if len(self.contents) > 0 else DataType.VOID
        return CompoundType(PrimitiveType.LIST, inner_type)

class BlockNode(ListNode):
    def __init__(self, contents: list[Node] = [], parent: Self | None = None):
        super().__init__(contents)
        self.idents = []
        self.parent = parent
    def __pretty_print__(self, printer):
        printer.append_ln('Block [(')
        printer.right()
        if self.idents:
            for definition in self.idents:
                printer.print(definition)
            printer.append_ln()
        for node in self.contents:
            printer.print(node)
        printer.left()
        printer.append_ln(')]')
    def data_type(self):
        return self.contents[-1].data_type() if len(self.contents) > 0 else DataType.VOID
    def get_idents(self):
        return self.idents + (self.parent.idents if self.parent is not None else [])

class Module:
    def __init__(self, entry_point: BlockNode):
        self.entry_point = entry_point
        extract_defines = lambda n: n.idents + [extract_defines(c) for c in n.contents if isinstance(c, BlockNode)]
        self.defines = extract_defines(self.entry_point)
    def __repr__(self):
        return repr(self.entry_point)
    def __pretty_print__(self, printer):
        return self.entry_point.__pretty_print__(printer)

class NumberNode(Node):
    def __init__(self, val: int):
        self.value = val
    def __pretty_print__(self, printer):
        printer.append_ln(f'Number ({self.value})')
    def data_type(self):
        return DataType.INT

class StringNode(Node):
    def __init__(self, val: str):
        self.value = val
    def __pretty_print__(self, printer):
        printer.append_ln(f'String "{self.value}"')
    def data_type(self):
        return DataType.STRING

class ReferenceNode(Node):
    def __init__(self, name: str):
        self.name = name
    def __pretty_print__(self, printer):
        printer.append_ln(f'Reference to ${self.name}')
    def data_type(self):
        return CompoundType(PrimitiveType.REF, DataType.UNKNOWN)

class StructNode(Node):
    def __init__(self):
        pass
    def __pretty_print__(self, printer):
        pass
    def data_type(self):
        pass
