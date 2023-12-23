from abc import ABC, abstractmethod

from brik.printer import Printer
from brik.syntax_tree import CallNode

class CallConvention(ABC):
    @abstractmethod
    def generate_call(self, p: Printer, call: CallNode):
        pass
    @abstractmethod
    def generate_func_open(self, p: Printer):
        pass
    @abstractmethod
    def generate_func_close(self, p: Printer):
        pass

class CdeclCallConvention(CallConvention):
    def generate_call(self, p: Printer, call: CallNode):
        
    pass

class MicrosoftCallConvention(CallConvention):
    pass
