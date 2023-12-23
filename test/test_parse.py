from unittest import TestCase
from brik.tokens import Token, TokenType
from brik.parse import ParseException, Parser
from brik.syntax_tree import AsmMacroNode, BlockNode, CallNode, NumberNode, ReferenceNode

class TestParser(TestCase):
    def test_next_is(self):
        # next_is number
        parser = Parser([Token(TokenType.NUMBER, 0, 0)])
        self.assertTrue(parser.next_is(TokenType.NUMBER))
        self.assertFalse(parser.next_is(TokenType.IDENT))
        self.assertFalse(parser.next_is(TokenType.RIGHT_BRACE))

        # next_is None
        parser = Parser([])
        self.assertFalse(parser.next_is(TokenType.NUMBER))

    def test_parse_list(self):
        # parse simple list
        parser = Parser([
            Token(TokenType.LEFT_PAREN, 0, '('),
            Token(TokenType.NUMBER, 1, 123),
            Token(TokenType.NUMBER, 2, 234),
            Token(TokenType.RIGHT_PAREN, 3, ')')
        ])
        list_node = parser.parse_list()
        self.assertListEqual(
            [
                NumberNode(123),
                NumberNode(234)
            ],
            list_node.contents
        )

        # parse empty list
        parser = Parser([
            Token(TokenType.LEFT_PAREN, 0, '('),
            Token(TokenType.RIGHT_PAREN, 1, ')')
        ])
        list_node = parser.parse_list()
        self.assertEqual(0, len(list_node.contents))

    def test_parse_list_throws(self):
        # missing open paren
        with self.assertRaises(ParseException):
            parser = Parser([])
            parser.parse_list()
        # missing close paren
        with self.assertRaises(ParseException):
            parser = Parser([Token(TokenType.LEFT_PAREN, 0, '(')])
            parser.parse_list()

    def test_parse_call(self):
        # parse simple call
        parser = Parser([
            Token(TokenType.LEFT_BRACKET, 0, '['),
            Token(TokenType.IDENT, 1, 'test_call'),
            Token(TokenType.RIGHT_BRACKET, 3, ']')
        ])
        call = parser.parse_call()
        self.assertIsInstance(call, CallNode)
        self.assertEqual('test_call', call.name)
        self.assertListEqual([], call.operands)

        # parse call with operand
        parser = Parser([
            Token(TokenType.LEFT_BRACKET, 0, '['),
            Token(TokenType.IDENT, 1, 'test_call'),
            Token(TokenType.NUMBER, 2, 123),
            Token(TokenType.RIGHT_BRACKET, 3, ']')
        ])
        call = parser.parse_call()
        self.assertIsInstance(call, CallNode)
        self.assertEqual('test_call', call.name)
        self.assertListEqual(
            [NumberNode(123)],
            call.operands
        )

        # parse asm call
        parser = Parser([
            Token(TokenType.LEFT_BRACKET, 0, '['),
            Token(TokenType.KEYWORD, 1, 'asm'),
            Token(TokenType.STRING, 2, 'test asm'),
            Token(TokenType.RIGHT_BRACKET, 3, ']')
        ])
        call = parser.parse_call()
        self.assertIsInstance(call, AsmMacroNode)
        self.assertEqual('test asm', call.asm)

        # parse def call
        parser = Parser([
            Token(TokenType.LEFT_BRACKET, 0, '['),
            Token(TokenType.KEYWORD, 1, 'def'),
            Token(TokenType.IDENT, 2, 'test'),
            Token(TokenType.RIGHT_BRACKET, 3, ']')
        ])
        parser.current_block = BlockNode([])
        call = parser.parse_call()
        self.assertIsInstance(call, ReferenceNode)
        self.assertEqual('test', call.name)

    def test_parse_call_throws(self):
        with self.assertRaises(ParseException):
            parser = Parser([])
            parser.parse_call()
        with self.assertRaises(ParseException):
            parser = Parser([Token(TokenType.LEFT_BRACKET, 0, '[')])
            parser.parse_call()
        with self.assertRaises(ParseException):
            parser = Parser([
                Token(TokenType.LEFT_BRACKET, 0, '['),
                Token(TokenType.IDENT, 1, 'test')
            ])
            parser.parse_call()

    def test_parse(self):
        parser = Parser([])
        module = parser.parse()
        self.assertIsNotNone(module)
        self.assertIsNotNone(module.entry_point)
        self.assertEqual(0, len(module.entry_point.contents))
