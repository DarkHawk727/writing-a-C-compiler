from itertools import count
from typing import Any, Dict, List

from frontend.ast_ir import (
    BinaryOp,
    BinaryOpType,
    Constant,
    Function,
    Program,
    UnaryOp,
    UnaryOpType,
)
from middle.tacky_ir import (
    TACKYBinaryOp,
    TACKYBinaryOpType,
    TACKYConstant,
    TACKYCopy,
    TACKYFunction,
    TACKYInstruction,
    TACKYJump,
    TACKYJumpIfNotZero,
    TACKYJumpIfZero,
    TACKYLabel,
    TACKYProgram,
    TACKYReturn,
    TACKYUnaryOp,
    TACKYUnaryOpType,
    TACKYValue,
    TACKYVariable,
)

_temp_counter = count(0)
_label_counter = count(0)


def make_temp():
    return f"tmp_{next(_temp_counter)}"


def make_label(prefix="L"):
    return f"{prefix}{next(_label_counter)}"


def _convert_uop(op: UnaryOpType) -> TACKYUnaryOpType:
    _UNARY_OP_MAP: Dict[UnaryOpType, TACKYUnaryOpType] = {
        UnaryOpType.COMPLEMENT: TACKYUnaryOpType.COMPLEMENT,
        UnaryOpType.NEGATION: TACKYUnaryOpType.NEGATION,
        UnaryOpType.NOT: TACKYUnaryOpType.NOT,
    }

    try:
        tacky_op = _UNARY_OP_MAP[op]
    except KeyError:
        raise TypeError(f"Unsupported binary operator: {op!r}")
    return tacky_op


def _convert_binaryop(op: BinaryOpType) -> TACKYBinaryOpType:
    _BINARY_OP_MAP: Dict[BinaryOpType, TACKYBinaryOpType] = {
        BinaryOpType.ADD: TACKYBinaryOpType.ADD,
        BinaryOpType.SUBTRACT: TACKYBinaryOpType.SUBTRACT,
        BinaryOpType.MULTIPLY: TACKYBinaryOpType.MULTIPLY,
        BinaryOpType.DIVIDE: TACKYBinaryOpType.DIVIDE,
        BinaryOpType.REMAINDER: TACKYBinaryOpType.REMAINDER,
        BinaryOpType.BITWISE_AND: TACKYBinaryOpType.BITWISE_AND,
        BinaryOpType.BITWISE_OR: TACKYBinaryOpType.BITWISE_OR,
        BinaryOpType.BITWISE_XOR: TACKYBinaryOpType.BITWISE_XOR,
        BinaryOpType.L_SHIFT: TACKYBinaryOpType.L_SHIFT,
        BinaryOpType.R_SHIFT: TACKYBinaryOpType.R_SHIFT,
        BinaryOpType.LOGICAL_AND: TACKYBinaryOpType.LOGICAL_AND,
        BinaryOpType.LOGICAL_OR: TACKYBinaryOpType.LOGICAL_OR,
        BinaryOpType.EQUAL: TACKYBinaryOpType.EQUAL,
        BinaryOpType.NOT_EQUAL: TACKYBinaryOpType.NOT_EQUAL,
        BinaryOpType.LESS_THAN: TACKYBinaryOpType.LESS_THAN,
        BinaryOpType.LESS_THAN_OR_EQUAL: TACKYBinaryOpType.LESS_THAN_OR_EQUAL,
        BinaryOpType.GREATER_THAN: TACKYBinaryOpType.GREATER_THAN,
        BinaryOpType.GREATER_THAN_OR_EQUAL: TACKYBinaryOpType.GREATER_THAN_OR_EQUAL,
    }

    try:
        tacky_op = _BINARY_OP_MAP[op]
    except KeyError:
        raise TypeError(f"Unsupported binary operator: {op!r}")
    return tacky_op


def emit_TACKY(expr: Any, instructions: List) -> TACKYValue:
    match expr:
        case Constant(val):
            return TACKYConstant(val)

        case UnaryOp(op, inner_expr):
            tacky_op = _convert_uop(op)
            src = emit_TACKY(inner_expr, instructions)
            dst_name = make_temp()
            dst = TACKYVariable(dst_name)
            instructions.append(TACKYUnaryOp(tacky_op, src, dst))
            return dst

        case BinaryOp(op, e1, e2) if op in (
            BinaryOpType.LOGICAL_AND,
            BinaryOpType.LOGICAL_OR,
        ):
            dst = TACKYVariable(make_temp())
            end_label = make_label("sc_end")

            if op == BinaryOpType.LOGICAL_AND:
                # dst = 0; if (e1 == 0) goto end; if (e2 == 0) goto end; dst = 1; end:
                instructions.append(TACKYCopy(TACKYConstant(0), dst))
                v1 = emit_TACKY(e1, instructions)
                instructions.append(TACKYJumpIfZero(v1, end_label))
                v2 = emit_TACKY(e2, instructions)
                instructions.append(TACKYJumpIfZero(v2, end_label))
                instructions.append(TACKYCopy(TACKYConstant(1), dst))
                instructions.append(TACKYLabel(end_label))
                return dst
            else:
                # dst = 0; if (e1 != 0) { dst = 1; goto end; } if (e2 != 0) { dst = 1; } end:
                instructions.append(TACKYCopy(TACKYConstant(0), dst))
                v1 = emit_TACKY(e1, instructions)
                set_true = make_label("sc_true")
                instructions.append(TACKYJumpIfNotZero(v1, set_true))
                v2 = emit_TACKY(e2, instructions)
                instructions.append(TACKYJumpIfNotZero(v2, set_true))
                instructions.append(TACKYJump(end_label))
                instructions.append(TACKYLabel(set_true))
                instructions.append(TACKYCopy(TACKYConstant(1), dst))
                instructions.append(TACKYLabel(end_label))
                return dst

        # All binops except && and ||
        case BinaryOp(op, e1, e2):
            tacky_binop = _convert_binaryop(op)
            v1 = emit_TACKY(e1, instructions)
            v2 = emit_TACKY(e2, instructions)
            dst_name = make_temp()
            dst = TACKYVariable(dst_name)
            instructions.append(TACKYBinaryOp(tacky_binop, v1, v2, dst))
            return dst

        case _:
            raise NotImplementedError(f"emit_tacky: {type(expr).__name__}")


def convert_AST_to_TACKY(node: Any) -> Any:
    match node:
        case Program(main_func):
            func_def = convert_AST_to_TACKY(main_func)
            return TACKYProgram(func_def)

        case Function(n, b):
            instrs: List[TACKYInstruction] = []
            instrs.append(TACKYReturn(emit_TACKY(b.return_val, instrs)))
            return TACKYFunction(n.name, instrs)

        case _:
            raise NotImplementedError(f"convert_AST_to_TACKY: {type(node).__name__}")
