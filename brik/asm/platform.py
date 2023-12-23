from abc import ABC, abstractmethod
from enum import Enum
from typing import Self

from brik.printer import Printer

class Syscall(Enum):
    READ = 0
    WRITE = 1
    OPEN = 2
    CLOSE = 3
    STAT = 4
    FSTAT = 5
    LSTAT = 6
    POLL = 7
    LSEEK = 8
    MMAP = 9
    MPROTECT = 10
    MUNMAP = 11
    EXIT = 12

class CompilerPlatform(Enum):
    LINUX_X86_32 = 0
    LINUX_X86_64 = 1
    WINDOWS_X86_32 = 2
    WINDOWS_X86_64 = 3

class Platform(ABC):
    @abstractmethod
    def get_word_size(self)-> int:
        pass
    @abstractmethod
    def get_reg_prefix(self)-> str:
        pass
    @abstractmethod
    def get_assembler_format(self)-> str:
        pass

    @abstractmethod
    def make_syscall(self, printer: Printer, syscall: Syscall, *data):
        pass

    def make_exit(self, printer: Printer, exit_code: int):
        self.make_syscall(printer, Syscall.EXIT, exit_code)

    _registers = ['ax','bx','cx','dx','sp','bp','si','di']
    def __getattribute__(self, name: str):
        if name != 'get_register':
            val = self.get_register(name)
            if val: return val
        return super().__getattribute__(name)
    def get_register(self, name: str):
        if len(name) == 2 and name.lower() in Platform._registers:
            return f'{self.get_reg_prefix()}{name.lower()}'
        else: return None

    def make_stack_frame(self, printer: Printer):
        printer.append_ln(f'push {self.bp}')
        printer.append_ln(f'mov {self.bp}, {self.sp}')
    def end_stack_frame(self, printer: Printer):
        printer.append_ln(f'mov {self.sp}, {self.bp}')
        printer.append_ln(f'pop {self.bp}')

def get_platform(platform: CompilerPlatform)-> Platform:
    if platform == CompilerPlatform.LINUX_X86_32:
        return PlatformLinux32()
    elif platform == CompilerPlatform.LINUX_X86_64:
        return PlatformLinux64()
    elif platform == CompilerPlatform.WINDOWS_X86_32:
        return PlatformWin32()
    elif platform == CompilerPlatform.WINDOWS_X86_64:
        return PlatformWin64()
    else:
        raise Exception('Could not recognize platform')

class PlatformLinux(Platform):
    pass

class PlatformLinux32(PlatformLinux):
    def get_word_size(self)-> int:
        return 4
    def get_reg_prefix(self)-> str:
        return 'e'
    def get_assembler_format(self)-> str:
        return 'elf32'

    def make_syscall(self, printer: Printer, syscall: Syscall, *data):
        if syscall == Syscall.EXIT:
            printer.append_ln(f'mov {self.bx}, {data[0]}')
            printer.append_ln(f'mov {self.ax}, 1d')

        printer.append_ln('int 0x80')

class PlatformLinux64(PlatformLinux):
    def get_word_size(self)-> int:
        return 8
    def get_reg_prefix(self)-> str:
        return 'r'
    def get_assembler_format(self)-> str:
        return 'elf64'

    def make_syscall(self, printer: Printer, syscall: Syscall, *data):
        if syscall == Syscall.EXIT:
            printer.append_ln(f'mov {self.di}, {data[0]}')
            printer.append_ln(f'mov {self.ax}, 60d')

        printer.append_ln('syscall')

class PlatformWin(Platform):
    pass

class PlatformWin32(PlatformWin):
    def get_word_size(self)-> int:
        return 4
    def get_reg_prefix(self)-> str:
        return 'e'
    def get_assembler_format(self)-> str:
        return 'win32'

    def make_syscall(self, printer: Printer, syscall: Syscall, *data):
        if syscall == Syscall.EXIT:
            printer.append_ln(f'mov {self.bx}, {data[0]}')
            printer.append_ln(f'mov {self.ax}, 1d')

        printer.append_ln('int 0x80')

class PlatformWin64(PlatformWin):
    def get_word_size(self)-> int:
        return 8
    def get_reg_prefix(self)-> str:
        return 'r'
    def get_assembler_format(self)-> str:
        return 'win64'

    def make_syscall(self, printer: Printer, syscall: Syscall, *data):
        if syscall == Syscall.EXIT:
            printer.append_ln(f'mov {self.di}, {data[0]}')
            printer.append_ln(f'mov {self.ax}, 60d')

        printer.append_ln('syscall')
