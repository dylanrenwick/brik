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
        p.append_ln('SECTION .text')
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

class AsmLiteral(AsmNode):
    def __init__(self, value: str):
        self.value = value
    def data_type(self)-> DataType:
        return super().data_type()

class AsmExpr(AsmNode):
    def __init__(self, datatype: DataType):
        self.datatype = datatype
    def data_type(self)-> DataType:
        return self.datatype
class AsmInt(AsmExpr):
    def __init__(self, val: int):
        super().__init__(DataType.INT)
        self.value = val
class AsmString(AsmExpr):
    def __init__(self, val: str):
        super().__init__(DataType.STRING)
        self.value = val

class AsmBlock(AsmExpr):
    def __init__(self, name: str, contents: list[AsmNode]):
        super().__init__(DataType.UNKNOWN if len(contents) < 1 else contents[-1].data_type())
        self.label = name
        self.contents = contents

class AsmCall(AsmExpr):
    def __init__(self, name: str, datatype: DataType, operands: list[AsmExpr]):
        super().__init__(datatype)
        self.target = name
        self.operands = operands

class AsmModule:
    def __init__(self):
        self.data = DataSection()
        self.text = []
    def get_block(self, label: str)-> Tuple[AsmBlock, CallDefinition] | None:
        for block in self.text:
            if block[0].label == label: return block
        return None
    def add_block(self, block: AsmBlock, define: CallDefinition):
        self.text.append((block, define))