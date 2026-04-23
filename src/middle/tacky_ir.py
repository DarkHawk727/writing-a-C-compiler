from __future__ import annotations

from enum import Enum, auto
from typing import List, NamedTuple, TypeAlias


class TACKYConstant(NamedTuple):
    value: int


class TACKYVariable(NamedTuple):
    identifier: str


TACKYValue: TypeAlias = TACKYConstant | TACKYVariable


class TACKYUnaryOpType(Enum):
    COMPLEMENT = auto()
    NEGATION = auto()
    NOT = auto()


class TACKYUnaryOp(NamedTuple):
    unary_operator: TACKYUnaryOpType
    source: TACKYValue
    destination: TACKYValue


class TACKYBinaryOpType(Enum):
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


class TACKYBinaryOp(NamedTuple):
    binary_operator: TACKYBinaryOpType
    source_1: TACKYValue
    source_2: TACKYValue
    destination: TACKYValue


class TACKYReturn(NamedTuple):
    value: TACKYValue


class TACKYCopy(NamedTuple):
    src: TACKYValue
    dst: TACKYValue


class TACKYJump(NamedTuple):
    target: str


class TACKYJumpIfZero(NamedTuple):
    condition: TACKYValue
    target: str


class TACKYJumpIfNotZero(NamedTuple):
    condition: TACKYValue
    target: str


class TACKYLabel(NamedTuple):
    identifier: str


TACKYInstruction: TypeAlias = (
    TACKYReturn
    | TACKYUnaryOp
    | TACKYBinaryOp
    | TACKYCopy
    | TACKYJump
    | TACKYJumpIfZero
    | TACKYJumpIfNotZero
    | TACKYLabel
)


class TACKYFunction(NamedTuple):
    identifier: str
    instructions: List[TACKYInstruction]


class TACKYProgram(NamedTuple):
    function_definition: TACKYFunction
