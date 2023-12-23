from abc import ABC, abstractmethod
from typing import Tuple

from brik.datatypes import DataType
from brik.definitions import CallDefinition
from brik.printer import Printer

class DataSection:
    def __init__(self):
        self.data = {}
        self.counter = 1
        pass
    def __str__(self)-> str:
        p = Printer('  ')
        p.append_ln('section .data')
        for name in self.data:
            p.append_ln(f'{name}:\tdb "{self.data[name]}",10')
        return str(p)

    def add(self, name: str, val: str):
        self.data[name] = val
    def add_autoname(self, val: str)-> str:
        name = f'auto_str_{self.counter}'
        self.add(name, val)
        return name

class AsmNode(ABC):
    @abstractmethod
    def data_type(self)-> DataType:
        return DataType.UNKNOWN
    @abstractmethod
    def __pretty_print__(self, printer: Printer):
        pass

class AsmLiteral(AsmNode):
    def __init__(self, asm: str):
        self.asm = asm
    def data_type(self)-> DataType:
        return super().data_type()
    def __pretty_print__(self, printer: Printer):
        printer.append_ln('#asm:')
        printer.right()
        printer.append_ln(self.asm)
        printer.left()

class AsmExpr(AsmNode):
    def __init__(self, datatype: DataType):
        self.datatype = datatype
    def data_type(self)-> DataType:
        return self.datatype
class AsmInt(AsmExpr):
    def __init__(self, val: int):
        super().__init__(DataType.INT)
        self.value = val
    def __pretty_print__(self, printer: Printer):
        printer.append(str(self.value))
class AsmString(AsmExpr):
    def __init__(self, val: str):
        super().__init__(DataType.STRING)
        self.value = val
    def __pretty_print__(self, printer: Printer):
        printer.append(f'"{self.value}"')

class AsmBlock(AsmExpr):
    def __init__(self, name: str, contents: list[AsmNode]):
        super().__init__(DataType.UNKNOWN if len(contents) < 1 else contents[-1].data_type())
        self.label = name
        self.contents = contents
    def __pretty_print__(self, printer: Printer):
        printer.append_ln(f'{self.label}:')
        printer.right()
        for child in self.contents:
            printer.print(child)
        printer.left()

class AsmCall(AsmExpr):
    def __init__(self, name: str, datatype: DataType, operands: list[AsmExpr]):
        super().__init__(datatype)
        self.target = name
        self.operands = operands
    def __pretty_print__(self, printer: Printer):
        printer.append(f'Call {self.target} (')
        for i in range(0, len(self.operands)):
            printer.print(self.operands[i])
            if i < len(self.operands) - 1:
                printer.append(' ')
        printer.append_ln(')')

class AsmModule:
    def __init__(self):
        self.data = DataSection()
        self.text: list[Tuple[AsmBlock, CallDefinition]] = []
    def get_block(self, label: str)-> Tuple[AsmBlock, CallDefinition] | None:
        for block in self.text:
            if block[0].label == label: return block
        return None
    def add_block(self, block: AsmBlock, define: CallDefinition):
        self.text.append((block, define))
    def __pretty_print__(self, printer: Printer):
        printer.append_ln(str(self.data))
        for block in self.text:
            printer.append(block[0].label)
            if block[1].pattern is not None and len(block[1].pattern.args) > 0:
                printer.append(f' {str(block[1].pattern)}')
            printer.append_ln(':')
            printer.right()
            for child in block[0].contents:
                printer.print(child)
            printer.left()
            printer.append_ln()
