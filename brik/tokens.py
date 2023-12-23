from enum import Enum
from typing import Any

from brik.debug import Debug

class TokenType(Enum):
    LEFT_BRACKET = 0
    RIGHT_BRACKET = 1
    LEFT_BRACE = 2
    RIGHT_BRACE = 3
    LEFT_PAREN = 4
    RIGHT_PAREN = 5
    PATTERN_START = 6
    PATTERN_END = 7

    IDENT = 8
    KEYWORD = 9
    NUMBER = 10
    STRING = 11
    CHAIN = 12
    COMMA = 13
    COLON = 14

class Token:
    def __init__(self, tok_type: TokenType, pos: int, val: Any):
        self.type = tok_type
        self.pos = pos
        self.value = val
    def __eq__(self, other)-> bool:
        return self.type == other.type and self.pos == other.pos and self.value == other.value
    def __str__(self)-> str:
        return f'{{ {self.type.name} {self.pos} {self.value} }}'
    def __repr__(self)-> str:
        return str(self)

class Tokenizer(Debug):
    _symbols = {
        '[': TokenType.LEFT_BRACKET,
        ']': TokenType.RIGHT_BRACKET,
        '{': TokenType.LEFT_BRACE,
        '}': TokenType.RIGHT_BRACE,
        '(': TokenType.LEFT_PAREN,
        ')': TokenType.RIGHT_PAREN,
        '<': TokenType.PATTERN_START,
        '>': TokenType.PATTERN_END,
        '$': TokenType.CHAIN,
        ',': TokenType.COMMA,
        ':': TokenType.COLON
    }
    _keywords = [
        'asm',
        'def'
    ]
    _whitespace = ' \t\r\n'
    _number = '0123456789'
    _ident_start = 'abcdefghijklmnopqrstuvwxyz_+-*%^&|/'
    _ident = f'{_ident_start}{_number}'

    def __init__(self, source: str, debug: bool=False):
        super(Tokenizer, self).__init__(debug)
        self.source = source
        self.pos = 0
        self.start = 0
        self.tokens = []

    def at_end(self)-> bool:
        return self.pos >= len(self.source)

    def peek(self)-> str:
        if self.at_end(): raise Exception('Unexpected end of file')
        return self.source[self.pos]
    def next(self)-> str:
        val = self.peek()
        self.pos += 1 if val else 0
        return val

    def skip_whitespace(self):
        while not self.at_end() and self.peek() in Tokenizer._whitespace:
            self.next()

    def tokenize(self)-> list[Token]:
        self.v_print(f'Starting tokenization, source is {len(self.source)} chars')
        self.skip_whitespace()
        while not self.at_end():
            self.start = self.pos
            self.tokens.append(self.tokenize_next())
            self.v_print(f'Tokenized {self.start}-{self.pos} as {self.tokens[-1]}')
            self.skip_whitespace()
        self.v_print(f'Tokenized {len(self.tokens)} tokens')
        return self.tokens

    def tokenize_next(self)-> Token:
        c = self.next()
        if c is None:
            raise Exception('Unexpected end of file')
        elif c in Tokenizer._symbols:
            return Token(Tokenizer._symbols[c], self.start, c)
        elif c == '"':
            return self.tokenize_string()
        elif c == '#':
            return self.tokenize_keyword()
        elif Tokenizer.is_ident_start(c):
            return self.tokenize_ident(c)
        elif Tokenizer.is_number(c):
            return self.tokenize_number(c)
        else:
            raise Exception(f'Unrecognized character {c}')

    def tokenize_number(self, num: str)-> Token:
        while not self.at_end() and Tokenizer.is_number(self.peek()):
            num += self.next()
        return Token(TokenType.NUMBER, self.start, int(num))

    def tokenize_ident(self, ident: str)-> Token:
        while not self.at_end() and Tokenizer.is_ident(self.peek()):
            ident += self.next()
        return Token(TokenType.IDENT, self.start, ident)

    def tokenize_keyword(self)-> Token:
        ident = ''
        while not self.at_end() and Tokenizer.is_ident(self.peek()):
            ident += self.next()
        if ident not in Tokenizer._keywords:
            raise Exception(f'Unrecognized keyword: {ident}')
        return Token(TokenType.KEYWORD, self.start, ident)

    def tokenize_string(self)-> Token:
        is_escaped = False
        string = ''
        while not self.at_end() and (self.peek() != '"' or is_escaped):
            c = self.next()
            if c == '\\':
                is_escaped = True
                continue
            elif is_escaped:
                is_escaped = False
            string += c

        if self.at_end():
            raise Exception('Found end of code while tokenizing string')

        self.next()
        return Token(TokenType.STRING, self.start, string)

    @staticmethod
    def is_number(c: str)-> bool:
        return c in Tokenizer._number
    @staticmethod
    def is_ident_start(c: str)-> bool:
        return c in Tokenizer._ident_start
    @staticmethod
    def is_ident(c: str)-> bool:
        return c in Tokenizer._ident
