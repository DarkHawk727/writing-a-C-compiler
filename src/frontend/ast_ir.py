from __future__ import annotations

from enum import Enum, auto
from typing import List, NamedTuple


class Constant(NamedTuple):
    val: int


class Identifier(NamedTuple):
    name: str


class Return(NamedTuple):
    return_val: Expression


class Program(NamedTuple):
    function_definition: Function


class UnaryOpType(Enum):
    NEGATION = auto()
    COMPLEMENT = auto()
    NOT = auto()


class UnaryOp(NamedTuple):
    operator: UnaryOpType
    inner_exp: Expression


class BinaryOpType(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    REMAINDER = auto()
    BITWISE_AND = auto()
    BITWISE_OR = auto()
    BITWISE_XOR = auto()
    L_SHIFT = auto()
    R_SHIFT = auto()
    LOGICAL_AND = auto()
    LOGICAL_OR = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUAL = auto()


class BinaryOp(NamedTuple):
    operator: BinaryOpType
    l_exp: Expression
    r_exp: Expression


class Variable(NamedTuple):
    identifier: str


class Assignment(NamedTuple):
    lhs: Expression
    rhs: Expression


class NULL(NamedTuple):
    pass


Expression = Constant | Variable | UnaryOp | BinaryOp | Assignment

Statement = Return | Expression | NULL


class Declaration(NamedTuple):
    identifier: Identifier
    initializer: Expression | NULL


BlockItem = Statement | Declaration


class Function(NamedTuple):
    name: Identifier
    body: List[BlockItem]
