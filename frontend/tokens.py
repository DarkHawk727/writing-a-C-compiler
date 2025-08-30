from enum import Enum, auto
from typing import NamedTuple


class TokenType(Enum):
    IDENTIFIER = auto()
    CONSTANT = auto()
    INT_KEYWORD = auto()
    VOID_KEYWORD = auto()
    RETURN = auto()
    L_PAREN = auto()
    R_PAREN = auto()
    L_BRACE = auto()
    R_BRACE = auto()
    SEMICOLON = auto()
    TILDE = auto()
    DECREMENT = auto()
    PLUS_SIGN = auto()
    ASTERISK = auto()
    FORWARD_SLASH = auto()
    MINUS_SIGN = auto()
    PERCENT_SIGN = auto()
    AMPERSAND = auto()
    VERTICAL_BAR = auto()
    CARET = auto()
    L_SHIFT = auto()
    R_SHIFT = auto()
    EXCLAMATION = auto()
    DOUBLE_AMPERSAND = auto()
    DOUBLE_VERTICAL_BAR = auto()
    DOUBLE_EQUAL_SIGNS = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()
    GREATER_THAN_OR_EQUAL = auto()


Token = NamedTuple("Token", [("type", TokenType), ("value", "str")])
