from unittest import TestCase
from brik.tokens import Token, Tokenizer, TokenType

class TestTokenizer(TestCase):
    def test_empty_tokens(self):
        tokens = Tokenizer('').tokenize()
        self.assertListEqual([], tokens)
    
    def test_symbols(self):
        self.assertListEqual(
            [
                Token(TokenType.LEFT_BRACKET, 0, '['),
                Token(TokenType.RIGHT_BRACKET, 1, ']'),
                Token(TokenType.LEFT_BRACE, 2, '{'),
                Token(TokenType.RIGHT_BRACE, 3, '}'),
                Token(TokenType.LEFT_PAREN, 4, '('),
                Token(TokenType.RIGHT_PAREN, 5, ')'),
                Token(TokenType.CHAIN, 6, '$')
            ],
            Tokenizer('[]{}()$').tokenize()
        )

    def test_idents(self):
        self.assertListEqual(
            [
                Token(TokenType.IDENT, 0, 'hello'),
                Token(TokenType.IDENT, 6, '%world'),
                Token(TokenType.IDENT, 13, '&h0w')
            ],
            Tokenizer('hello %world &h0w').tokenize()
        )

    def test_numbers(self):
        self.assertListEqual(
            [
                Token(TokenType.NUMBER, 0, 123),
                Token(TokenType.NUMBER, 4, 456)
            ],
            Tokenizer('123 0456').tokenize()
        )

    def test_strings(self):
        self.assertListEqual(
            [
                Token(TokenType.STRING, 0, 'string'),
                Token(TokenType.STRING, 9, 'str"ing'),
                Token(TokenType.STRING, 20, '[]{}()$')
            ],
            Tokenizer('"string" "str\\"ing" "[]{}()$"').tokenize()
        )

    def test_ignore_whitespace(self):
        self.assertListEqual(
            [
                Token(TokenType.LEFT_BRACKET, 3, '['),
                Token(TokenType.RIGHT_BRACKET, 6, ']'),
                Token(TokenType.LEFT_BRACE, 10, '{'),
                Token(TokenType.RIGHT_BRACE, 13, '}'),
                Token(TokenType.LEFT_PAREN, 16, '('),
                Token(TokenType.RIGHT_PAREN, 22, ')'),
                Token(TokenType.CHAIN, 26, '$')
            ],
            Tokenizer('   [\t ] \r {  }  (     ) \n $ ').tokenize()
        )