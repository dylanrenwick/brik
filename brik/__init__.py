import os
from typing import Tuple

from brik.asm.generation import AsmGenerator
from brik.asm.platform import CompilerPlatform, get_platform
from brik.asm.syntax_tree import AsmModule
from brik.asm.transpile import Transpiler
from brik.debug import Debug
from brik.parse import Parser
from brik.printer import Printer
from brik.syntax_tree import Module
from brik.tokens import Token, Tokenizer

class BrikOpts:
    def __init__(self,
                 name: str,
                 platform: CompilerPlatform,
                 out_dir: str = 'bin',
                 debug: bool = False):
        self.name = name
        self.platform = platform
        self.out_dir = out_dir
        self.debug = debug

class Brik(Debug):
    def __init__(self, opts: BrikOpts):
        super().__init__(opts.debug)
        self.platform = get_platform(opts.platform)
        self.name = opts.name
        self.out_dir = opts.out_dir
        self.create_out_dir()

    def create_out_dir(self):
        try:
            os.mkdir(self.bin_path())
            os.mkdir(self.asm_path())
            os.mkdir(self.obj_path())
            os.mkdir(self.out_path())
        except FileExistsError:
            pass
    def bin_path(self)-> str:
        return self.out_dir
    def asm_path(self)-> str:
        return f'{self.out_dir}/asm'
    def obj_path(self)-> str:
        return f'{self.out_dir}/obj'
    def out_path(self)-> str:
        return f'{self.out_dir}/out'

    def compile(self, source: str)-> str:
        return self.compile_all(source)[-1]
    def compile_all(self, source: str)-> Tuple[list[Token], Module, AsmModule, str, str, str]:
        tokens = self.tokenize(source)
        self.v_print(tokens)
        module = self.parse(tokens)
        p = Printer('  ')
        p.print(module)
        self.v_print(str(p))
        asm_mod = self.transpile(module)
        p.clear()
        p.print(asm_mod)
        self.v_print(str(p))
        asm_file_path = self.generate_asm(asm_mod)
        obj_file_path = self.assemble(asm_file_path)
        out_file_path = self.link(obj_file_path)
        return (tokens, module, asm_mod, asm_file_path, obj_file_path, out_file_path)
        
    def tokenize(self, source: str)-> list[Token]:
        tokenizer = Tokenizer(source, self.debug)
        return tokenizer.tokenize()
    def parse(self, tokens: list[Token])-> Module:
        parser = Parser(tokens, self.debug)
        return parser.parse()
    def transpile(self, module: Module)-> AsmModule:
        transpiler = Transpiler(self.debug)
        return transpiler.transpile(module)

    def generate_asm(self, mod: AsmModule)-> str:
        generator = AsmGenerator(self.platform, self.debug)
        asm = generator.generate_module(mod)
        path = f'{self.asm_path()}/{self.name}.asm'
        with open(path, 'w') as f:
            f.write(asm)
            f.flush()
        return path
    def assemble(self, asm_file_path: str)-> str:
        path = f'{self.obj_path()}/{self.name}.o'
        os.system(f'nasm -f {self.platform.get_assembler_format()} -o {path} {asm_file_path}')
        return path
    def link(self, obj_file_path: str)-> str:
        path = f'{self.out_path()}/{self.name}.exe'
        os.system(f'link /SUBSYSTEM:CONSOLE /ENTRY:_start /OUT:{path} {obj_file_path}')
        return path


