from __future__ import annotations

import itertools
from enum import Enum, auto
from typing import Any, List, Literal, NamedTuple, TypeAlias


class OffsetAllocator(dict):
    def __init__(self, start=-4, step=-4) -> None:
        super().__init__()
        self.counter = itertools.count(start, step)
        self.max_offset = start

    def __missing__(self, var_name: str) -> int:
        offset = next(self.counter)
        self[var_name] = offset
        self.max_offset = offset
        return offset


class AssemblyFunction(NamedTuple):
    name: str
    instructions: List[Any]
    offsets: OffsetAllocator


class AssemblyProgram(NamedTuple):
    function_definition: AssemblyFunction


class AssemblyImmediate(NamedTuple):
    value: int | str


class AssemblyMov(NamedTuple):
    exp: AssemblyRegister | AssemblyImmediate | AssemblyPseudoRegister | AssemblyStack
    register: Operand


class AssemblyPop(NamedTuple):
    register: str


class AssemblyRet(NamedTuple):
    pass


class AssemblyUnaryOpType(Enum):
    COMPLEMENT = auto()
    NEGATION = auto()


class AssemblyUnary(NamedTuple):
    unary_operator: AssemblyUnaryOpType
    operand: Operand


class AssemblyConditionCode(Enum):
    E = auto()
    NE = auto()
    G = auto()
    GE = auto()
    L = auto()
    LE = auto()


class AssemblyRegister(Enum):
    AX = auto()
    R10 = auto()
    DX = auto()
    R11 = auto()


class AssemblyStack(NamedTuple):
    offset: int


class AssemblyPseudoRegister(NamedTuple):
    identifier: str


Operand: TypeAlias = (
    AssemblyImmediate | AssemblyRegister | AssemblyPseudoRegister | AssemblyStack
)


class AssemblyCompare(NamedTuple):
    operand_1: Operand
    operand_2: Operand


class AssemblyJump(NamedTuple):
    identifier: str


class AssemblyJumpConditionCode(NamedTuple):
    cond_code: AssemblyConditionCode
    identifier: str


class AssemblySetConditionCode(NamedTuple):
    cond_code: AssemblyConditionCode
    operand_1: Operand


class AssemblyLabel(NamedTuple):
    identifier: str


class AssemblyBinaryOpType(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    BITWISE_AND = auto()
    BITWISE_OR = auto()
    BITWISE_XOR = auto()
    L_SHIFT = auto()
    R_SHIFT = auto()


class AssemblyBinaryOp(NamedTuple):
    binary_operator: AssemblyBinaryOpType
    operand_1: Operand
    operand_2: Operand


class AssemblyIDiv(NamedTuple):
    operand: Operand


# Convert Doubleword to Quadword
class AssemblyCdq(NamedTuple):
    pass


class AssemblyAllocateStack(NamedTuple):
    val: int
