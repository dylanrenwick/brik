from typing import Tuple
from brik.datatypes import DataType

class Pattern:
    def __init__(self, args: list[Tuple[str, DataType]]):
        self.args = args
    def __str__(self)-> str:
        return f'<{' '.join([f'{name}: {datatype.type.name.lower()}' for (name, datatype) in self.args])}>'

