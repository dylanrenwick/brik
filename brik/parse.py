from brik.syntax_tree import *
from brik.datatypes import DataType
from brik.debug import Debug
from brik.definitions import *
from brik.patterns import Pattern
from brik.tokens import Token, TokenType

class ParseException(Exception):
    pass

class Parser(Debug):
    def __init__(self, tokens, debug=False):
        super().__init__(debug)
        self.tokens = tokens
        self.pos = 0
        self.current_block = None

    def at_end(self)-> bool:
        return self.pos >= len(self.tokens)

    def peek(self, offset: int=0)-> Token:
        if self.at_end(): raise Exception('Unexpected end of tokens')
        return self.tokens[self.pos+offset]
    def next(self)-> Token:
        val = self.peek()
        self.pos += 1
        return val

    def expect(self, tok_type: TokenType, err_msg: str)-> Token:
        if self.next_is(tok_type):
            return self.next()
        else:
            raise ParseException(err_msg)
    def next_is(self, tok_type: TokenType)-> bool:
        t = self.peek()
        return t is not None and t.type == tok_type

    def wrap_in_block(self):
        if len(self.tokens) < 4 or not (self.tokens[0].type == TokenType.LEFT_BRACKET and self.tokens[1].type == TokenType.LEFT_PAREN and self.tokens[-1].type == TokenType.RIGHT_BRACKET and self.tokens[-2].type == TokenType.RIGHT_PAREN):
            self.tokens.insert(0, Token(TokenType.LEFT_BRACKET, -1, '['))
            self.tokens.insert(1, Token(TokenType.LEFT_PAREN, -1, '('))
            self.tokens.append(Token(TokenType.RIGHT_PAREN, -1, ')'))
            self.tokens.append(Token(TokenType.RIGHT_BRACKET, -1, ']'))

    def parse(self)-> Module:
        self.v_print(f'Starting parsing, {len(self.tokens)} tokens to parse')
        self.wrap_in_block()
        entry = self.parse_block()
        return Module(entry)

    def parse_next(self)-> Node:
        t = self.peek()
        if t.type == TokenType.LEFT_BRACKET:
            if self.peek(1).type == TokenType.LEFT_PAREN:
                return self.parse_block()
            else:
                return self.parse_call()
        #elif t.type == TokenType.LEFT_BRACE:
        #    return self.parse_struct()
        elif t.type == TokenType.LEFT_PAREN:
            return self.parse_list()
        elif t.type == TokenType.NUMBER:
            return NumberNode(self.next().value)
        elif t.type == TokenType.STRING:
            return StringNode(self.next().value)
        elif t.type == TokenType.IDENT:
            return ReferenceNode(self.next().value)
        else:
            raise ParseException(f'Cant parse from {t}')

    def parse_call(self)-> Node:
        self.v_print(f'Parsing call at {self.pos}')
        self.expect(TokenType.LEFT_BRACKET, 'Tried to parse call but did not find bracket')
        if self.next_is(TokenType.LEFT_PAREN):
            self.pos -= 1
            return self.parse_block()

        if self.next_is(TokenType.KEYWORD):
            name_tok = self.next()
            if name_tok.value == 'def':
                return self.parse_definition(name_tok)
            elif name_tok.value == 'asm':
                return self.parse_asm(name_tok)
            else:
                raise Exception(f'Unrecognized keyword {name_tok.value}')

        name_tok = self.expect(TokenType.IDENT, f'Could not parse call name')

        self.v_print(f'Parsing operands for call to {name_tok.value}')
        operands = []
        while not self.at_end() and not self.next_is(TokenType.RIGHT_BRACKET):
            operands.append(self.parse_next())

        self.expect(TokenType.RIGHT_BRACKET, f'Could not find closing bracket for call to {name_tok.value}')

        self.v_print(f'Parsed call to {name_tok.value} with {len(operands)} operands')
        return CallNode(name_tok.value, operands)

    def parse_list(self)-> ListNode:
        self.v_print(f'Parsing list at {self.pos}')
        self.expect(TokenType.LEFT_PAREN, 'Tried to parse list but did not find paren')

        contents = []
        while not self.at_end() and not self.next_is(TokenType.RIGHT_PAREN):
            contents.append(self.parse_next())

        self.expect(TokenType.RIGHT_PAREN, 'Could not find closing paren for list')

        self.v_print(f'Parsed list with {len(contents)} contents')
        return ListNode(contents)

    def parse_pattern(self)-> Pattern:
        self.expect(TokenType.PATTERN_START, 'Could not start pattern')
        args = []
        while not self.at_end() and not self.next_is(TokenType.PATTERN_END):
            arg_name = self.expect(TokenType.IDENT, 'Could not read pattern')
            datatype = None
            if self.next_is(TokenType.COLON):
                self.next()
                arg_type_tok = self.expect(TokenType.IDENT, 'Could not read pattern')
                arg_type = arg_type_tok.value.upper()
                datatype = getattr(DataType, arg_type)
            if not datatype:
                datatype = DataType.UNKNOWN
            args.append((arg_name.value, datatype))
        self.expect(TokenType.PATTERN_END, 'Could not end pattern')
        return Pattern(args)

    def parse_block(self)-> BlockNode:
        self.v_print(f'Parsing block at {self.pos}')
        self.expect(TokenType.LEFT_BRACKET, 'Tried to parse block but did not find bracket')
        self.expect(TokenType.LEFT_PAREN, 'Tried to parse block but did not find paren')

        block_node = BlockNode(parent=self.current_block)
        self.current_block = block_node

        contents = []
        while not self.at_end() and not self.next_is(TokenType.RIGHT_PAREN):
            next_node = self.parse_next()
            if next_node is not None:
                contents.append(next_node)
        block_node.contents = contents

        self.expect(TokenType.RIGHT_PAREN, 'Could not find closing paren for code block')
        self.expect(TokenType.RIGHT_BRACKET, 'Could not find closing bracket for code block')

        self.current_block = block_node.parent

        self.v_print(f'Parsed code block with {len(block_node.contents)} calls and {len(block_node.idents)} definitions')
        return block_node

    def parse_definition(self, name_tok: Token)-> ReferenceNode:
        if name_tok.type != TokenType.KEYWORD or name_tok.value != 'def':
            raise ParseException('Unexpected definition error')

        def_name_tok = self.expect(TokenType.IDENT, 'Could not find definition name')
        next_tok = self.peek()
        def_val = None
        if next_tok.type == TokenType.PATTERN_START:
            def_val = self.parse_pattern()
        elif next_tok.type != TokenType.RIGHT_BRACKET:
            def_val = self.parse_next()

        if def_val is None:
            self.v_print(f'Parsed definition of variable {def_name_tok.value}')
            definition = VarDefinition(def_name_tok.value, def_val)
        elif isinstance(def_val, BlockNode):
            self.v_print(f'Parsed definition of callable {def_name_tok.value}')
            definition = CallDefinition(def_name_tok.value, def_val)
        elif isinstance(def_val, Pattern):
            block = self.parse_next()
            if not isinstance(block, BlockNode):
                raise Exception('Unreachable')
            self.v_print(f'Parsed definition of callable {def_name_tok.value} with pattern')
            definition = CallDefinition(def_name_tok.value, block, def_val)
        else:
            self.v_print(f'Parsed definition of variable {def_name_tok.value} with value {def_val}')
            definition = VarDefinition(def_name_tok.value, def_val)

        self.expect(TokenType.RIGHT_BRACKET, 'Could not find closing bracket for definition')

        if self.current_block is None:
            raise ParseException('Cannot parse definition outside of block')
        self.current_block.idents.append(definition)
        self.v_print(f'Added definition to current block, block now has {len(self.current_block.idents)} definitions')
        return ReferenceNode(definition.name)

    def parse_asm(self, name_tok: Token)-> AsmMacroNode:
        if name_tok.type != TokenType.KEYWORD or name_tok.value != 'asm':
            raise ParseException('Unexpected asm error')

        contents = self.expect(TokenType.STRING, f'#asm builtin must take a string')
        self.expect(TokenType.RIGHT_BRACKET, 'Could not find closing bracket for call')

        asm: str = contents.value
        asm_lines = asm.split('\n')
        asm_lines = [line.strip() for line in asm_lines]
        asm = '\n'.join([line for line in asm_lines if len(line) > 0])

        return AsmMacroNode(asm)
