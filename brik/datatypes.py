from enum import Enum
from typing import Self

class PrimitiveType(Enum):
    UNKNOWN = 0
    VOID = 1
    USER_DEF = 2
    REF = 3
    LIST = 4
    STRUCT = 5
    CALL = 6
    INT = 7
    STRING = 8

class DataType:
    def __init__(self, data_type: PrimitiveType):
        self.type = data_type
    UNKNOWN: Self
    VOID: Self
    USER_DEF: Self
    REF: Self
    LIST: Self
    STRUCT: Self
    CALL: Self
    INT: Self
    STRING: Self
class CompoundType(DataType):
    def __init__(self, outer_type: PrimitiveType, *inner_types: DataType):
        super().__init__(outer_type)
        self.inner_types = list(inner_types)
class UserDefinedType(DataType):
    def __init__(self, name: str):
        super().__init__(PrimitiveType.USER_DEF)
        self.name = name

for tp in PrimitiveType:
    setattr(DataType, tp.name, DataType(tp))
