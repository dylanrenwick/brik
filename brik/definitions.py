from abc import ABC, abstractmethod

from brik.datatypes import *
from brik.patterns import Pattern
from brik.syntax_tree import BlockNode, Node

class Definition(ABC):
    def __init__(self, name: str):
        self.name = name
    def data_type(self)-> DataType:
        return CompoundType(PrimitiveType.REF, self.definition_type())
    @abstractmethod
    def __pretty_print__(self, printer):
        pass
    @abstractmethod
    def definition_type(self)-> DataType:
        pass

class CallDefinition(Definition):
    def __init__(self, name: str, contents: BlockNode, pattern: Pattern = Pattern([])):
        super().__init__(name)
        self.body = contents
        self.pattern = pattern
    def __pretty_print__(self, printer):
        printer.append(f'Define {self.name} as ')
        printer.print(self.body)
    def definition_type(self)-> DataType:
        return DataType.CALL

class VarDefinition(Definition):
    def __init__(self, name: str, value: Node | None):
        super().__init__(name)
        self.value = value
    def __pretty_print__(self, printer):
        printer.append(f'Define {self.name}')
        if self.value is not None:
            printer.append(' as ')
            printer.right()
            printer.print(self.value)
            printer.left()
        else:
            printer.append_ln()
    def definition_type(self)-> DataType:
        return self.value.data_type() if self.value else DataType.UNKNOWN
