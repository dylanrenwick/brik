from typing import Tuple
from brik.datatypes import DataType

class Pattern:
    def __init__(self, args: list[Tuple[str, DataType]]):
        self.args = args

