from __future__ import annotations

from typing import Dict, List

from src.frontend.ast_ir import *
from src.frontend.tokens import Token, TokenType


# This will remove the first element of tokens and pops it off. Modifies tokens
def _expect(expected_type: TokenType, tokens: List[Token]) -> Token:
    if not tokens:
        raise SyntaxError("Unexpected end of input")

    tok = tokens.pop(0)

    if expected_type != tok.type:
        raise SyntaxError(f"Syntax Error: Expected {expected_type}, got {tok}")
    return tok


_UOP_TABLE: Dict[TokenType, UnaryOpType] = {
    TokenType.MINUS_SIGN: UnaryOpType.NEGATION,
    TokenType.TILDE: UnaryOpType.COMPLEMENT,
    TokenType.EXCLAMATION: UnaryOpType.NOT,
}
_BINOP_TABLE: dict[TokenType, BinaryOpType] = {
    TokenType.PLUS_SIGN: BinaryOpType.ADD,
    TokenType.MINUS_SIGN: BinaryOpType.SUBTRACT,
    TokenType.ASTERISK: BinaryOpType.MULTIPLY,
    TokenType.FORWARD_SLASH: BinaryOpType.DIVIDE,
    TokenType.PERCENT_SIGN: BinaryOpType.REMAINDER,
    TokenType.AMPERSAND: BinaryOpType.BITWISE_AND,
    TokenType.VERTICAL_BAR: BinaryOpType.BITWISE_OR,
    TokenType.CARET: BinaryOpType.BITWISE_XOR,
    TokenType.L_SHIFT: BinaryOpType.L_SHIFT,
    TokenType.R_SHIFT: BinaryOpType.R_SHIFT,
    TokenType.DOUBLE_AMPERSAND: BinaryOpType.LOGICAL_AND,
    TokenType.DOUBLE_VERTICAL_BAR: BinaryOpType.LOGICAL_OR,
    TokenType.DOUBLE_EQUAL_SIGNS: BinaryOpType.EQUAL,
    TokenType.NOT_EQUAL: BinaryOpType.NOT_EQUAL,
    TokenType.LESS_THAN: BinaryOpType.LESS_THAN,
    TokenType.LESS_THAN_OR_EQUAL: BinaryOpType.LESS_THAN_OR_EQUAL,
    TokenType.GREATER_THAN: BinaryOpType.GREATER_THAN,
    TokenType.GREATER_THAN_OR_EQUAL: BinaryOpType.GREATER_THAN_OR_EQUAL,
}


def _parse_uop(tokens: List[Token]) -> UnaryOpType:
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    tok = tokens.pop(0)
    spec = _UOP_TABLE.get(tok.type)
    if spec is None:
        raise SyntaxError(f"Unknown unary operator: {tok!r}")

    return spec


def _parse_factor(tokens: List[Token]):
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    tok = tokens[0]

    if tok.type == TokenType.CONSTANT:
        tokens.pop(0)
        return Constant(int(tok.value))
    elif tok.type in _UOP_TABLE.keys():
        op = _parse_uop(tokens)
        inner_exp = _parse_factor(tokens)
        return UnaryOp(op, inner_exp)
    elif tok.type == TokenType.L_PAREN:
        tokens.pop(0)
        inner_exp = _parse_exp(tokens, 0)
        _expect(TokenType.R_PAREN, tokens)
        return inner_exp
    elif tok.type == TokenType.IDENTIFIER:
        tokens.pop(0)
        return Identifier(tok.value)
    else:
        raise SyntaxError(f"Malformed Factor: {tok}.")


def _parse_binop(tokens: List[Token]) -> BinaryOpType:
    if not tokens:
        raise SyntaxError("Unexpected end of input: expected a binary operator")

    tok = tokens[0]
    spec = _BINOP_TABLE.get(tok.type)
    if spec is None:
        raise SyntaxError(f"Unknown binary operator: {tok!r}")

    tokens.pop(0)

    return spec


def _precedence(tok: Token) -> int:
    _PRECEDENCE_TABLE: dict[TokenType, int] = {
        TokenType.ASTERISK: 70,
        TokenType.FORWARD_SLASH: 70,
        TokenType.PERCENT_SIGN: 70,
        TokenType.PLUS_SIGN: 60,
        TokenType.MINUS_SIGN: 60,
        TokenType.L_SHIFT: 55,
        TokenType.R_SHIFT: 55,
        TokenType.AMPERSAND: 40,
        TokenType.CARET: 35,
        TokenType.LESS_THAN: 35,
        TokenType.LESS_THAN_OR_EQUAL: 35,
        TokenType.GREATER_THAN: 35,
        TokenType.GREATER_THAN_OR_EQUAL: 35,
        TokenType.VERTICAL_BAR: 30,
        TokenType.DOUBLE_EQUAL_SIGNS: 30,
        TokenType.NOT_EQUAL: 30,
        TokenType.DOUBLE_AMPERSAND: 10,
        TokenType.DOUBLE_VERTICAL_BAR: 5,
        TokenType.ASSIGNMENT: 1,
    }
    try:
        return _PRECEDENCE_TABLE[tok.type]
    except KeyError:
        raise SyntaxError(f"Unknown Binary Operator: {tok}")


def _parse_exp(tokens: List[Token], min_precedence) -> Expression:
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    left = _parse_factor(tokens)
    tok = tokens[0]

    while tok.type in _BINOP_TABLE.keys() and _precedence(tok) >= min_precedence:
        if tok.type == TokenType.ASSIGNMENT:
            tokens.pop(0)
            right = _parse_exp(tokens, _precedence(tok))
            left = Assignment(left, right)
        else:
            op = _parse_binop(tokens)
            right = _parse_exp(tokens, _precedence(tok) + 1)
            left = BinaryOp(op, left, right)
        tok = tokens[0]
    return left


def _parse_statement(tokens: List[Token]) -> Statement:
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    _expect(TokenType.RETURN, tokens)
    return_val = _parse_exp(tokens, 0)
    _expect(TokenType.SEMICOLON, tokens)

    return Return(return_val)


def _parse_identifier(tokens: List[Token]) -> Identifier:
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    tok = tokens.pop(0)

    if tok.type != TokenType.IDENTIFIER:
        raise SyntaxError(f"Expected identifier, got {tok}")

    return Identifier(tok.value)


def _parse_block_item(tokens: List[Token]) -> BlockItem:
    if not tokens:
        raise SyntaxError("Unexpected end of input.")

    if tokens[0].type == TokenType.INT_KEYWORD:
        _expect(TokenType.INT_KEYWORD, tokens)
        identifier = _parse_identifier(tokens)

        if tokens[0].type == TokenType.SEMICOLON:
            tokens.pop(0)
            return Declaration(identifier, NULL())
        elif tokens[0].type == TokenType.ASSIGNMENT:
            tokens.pop(0)
            initializer = _parse_exp(tokens, 0)
            _expect(TokenType.SEMICOLON, tokens)
            return Declaration(identifier, initializer)
        else:
            raise SyntaxError(f"Expected ';' or '=', got {tokens[0]}")
    else:
        return _parse_statement(tokens)


def _parse_function(tokens: List[Token]) -> Function:
    if not tokens:
        raise SyntaxError("Unexpected enf of input.")

    _expect(TokenType.INT_KEYWORD, tokens)
    identifier = _parse_identifier(tokens)
    _expect(TokenType.L_PAREN, tokens)
    _expect(TokenType.VOID_KEYWORD, tokens)
    _expect(TokenType.R_PAREN, tokens)
    _expect(TokenType.L_BRACE, tokens)

    function_body = []
    while tokens[0].type != TokenType.R_BRACE:
        next_block_item = _parse_block_item(tokens)
        function_body.append(next_block_item)
    _expect(TokenType.R_BRACE, tokens)

    return Function(name=identifier, body=function_body)


def parse_program(tokens: List[Token]) -> Program:
    main = _parse_function(tokens)

    if tokens:
        raise SyntaxError(f"Unexpected tokens at end of program: {tokens}")

    return Program(main)
