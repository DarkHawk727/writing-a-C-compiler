from typing import Any, List, TypeAlias, cast

from src.backend.assembly_ir import *
from src.middle.tacky_ir import *

_ALU_BINOPS = {
    TACKYBinaryOpType.ADD: AssemblyBinaryOpType.ADD,
    TACKYBinaryOpType.SUBTRACT: AssemblyBinaryOpType.SUBTRACT,
    TACKYBinaryOpType.MULTIPLY: AssemblyBinaryOpType.MULTIPLY,
    TACKYBinaryOpType.BITWISE_AND: AssemblyBinaryOpType.BITWISE_AND,
    TACKYBinaryOpType.BITWISE_OR: AssemblyBinaryOpType.BITWISE_OR,
    TACKYBinaryOpType.BITWISE_XOR: AssemblyBinaryOpType.BITWISE_XOR,
    TACKYBinaryOpType.L_SHIFT: AssemblyBinaryOpType.L_SHIFT,
    TACKYBinaryOpType.R_SHIFT: AssemblyBinaryOpType.R_SHIFT,
}

_CMP_CC = {
    TACKYBinaryOpType.EQUAL: AssemblyConditionCode.E,
    TACKYBinaryOpType.NOT_EQUAL: AssemblyConditionCode.NE,
    TACKYBinaryOpType.GREATER_THAN: AssemblyConditionCode.G,
    TACKYBinaryOpType.GREATER_THAN_OR_EQUAL: AssemblyConditionCode.GE,
    TACKYBinaryOpType.LESS_THAN: AssemblyConditionCode.L,
    TACKYBinaryOpType.LESS_THAN_OR_EQUAL: AssemblyConditionCode.LE,
}


def _visit_value(tacky_value: TACKYValue) -> AssemblyImmediate | AssemblyPseudoRegister:
    if isinstance(tacky_value, TACKYConstant):
        return AssemblyImmediate(tacky_value.value)
    elif isinstance(tacky_value, TACKYVariable):
        return AssemblyPseudoRegister(tacky_value.identifier)
    raise TypeError(f"Unsupported TACKY value: {type(tacky_value).__name__}")


def _visit_unary(node: TACKYUnaryOp) -> List:
    dst = AssemblyPseudoRegister(node.destination.identifier)
    mov = AssemblyMov(_visit_value(node.source), dst)

    match node.unary_operator:
        case TACKYUnaryOpType.COMPLEMENT:
            u = AssemblyUnary(AssemblyUnaryOpType.COMPLEMENT, dst)

        case TACKYUnaryOpType.NEGATION:
            u = AssemblyUnary(AssemblyUnaryOpType.NEGATION, dst)

        case TACKYUnaryOpType.NOT:
            return [
                AssemblyCompare(AssemblyImmediate(0), _visit_value(node.source)),
                AssemblyMov(AssemblyImmediate(0), dst),
                AssemblySetConditionCode(AssemblyConditionCode.E, dst),
            ]

        case _:
            raise TypeError(f"Unsupported unary operator: {node.unary_operator!r}")

    return [mov, u]


def _emit_alu(s1, s2, dst, op_type) -> List:
    """dst = s1 <op> s2"""
    return [
        AssemblyMov(s1, dst),
        AssemblyBinaryOp(op_type, s2, dst),
    ]


def _visit_binary(node: TACKYBinaryOp) -> List:
    s1 = _visit_value(node.source_1)
    s2 = _visit_value(node.source_2)
    dst = AssemblyPseudoRegister(node.destination.identifier)
    op = node.binary_operator

    if op in _ALU_BINOPS:
        return _emit_alu(s1, s2, dst, _ALU_BINOPS[op])

    if op is TACKYBinaryOpType.DIVIDE:
        return [
            AssemblyMov(s1, AssemblyRegister.AX),
            AssemblyCdq(),
            AssemblyIDiv(s2),
            AssemblyMov(AssemblyRegister.AX, dst),
        ]

    if op is TACKYBinaryOpType.REMAINDER:
        return [
            AssemblyMov(s1, AssemblyRegister.AX),
            AssemblyCdq(),
            AssemblyIDiv(s2),
            AssemblyMov(AssemblyRegister.DX, dst),
        ]
    if op in _CMP_CC:
        return [
            AssemblyCompare(s2, s1),
            AssemblyMov(AssemblyImmediate(0), dst),
            AssemblySetConditionCode(_CMP_CC[op], dst),
        ]

    raise NotImplementedError(f"No visit logic in _visit_binary: {op}")


def _visit_return(tacky_return: TACKYReturn) -> List[AssemblyMov | AssemblyRet]:
    return [
        AssemblyMov(_visit_value(tacky_return.value), AssemblyRegister.AX),
        AssemblyRet(),
    ]


def _visit_jump(
    tacky_jump: TACKYJumpIfZero | TACKYJumpIfNotZero | TACKYJump,
) -> List:
    match tacky_jump:
        case TACKYJumpIfZero(val, target):
            return [
                AssemblyCompare(AssemblyImmediate(0), _visit_value(val)),
                AssemblyJumpConditionCode(AssemblyConditionCode.E, target),
            ]

        case TACKYJumpIfNotZero(val, target):
            return [
                AssemblyCompare(AssemblyImmediate(0), _visit_value(val)),
                AssemblyJumpConditionCode(AssemblyConditionCode.NE, target),
            ]

        case TACKYJump(target):
            return [AssemblyJump(target)]

        case _:
            raise NotImplementedError(f"No visit logic for {type(tacky_jump).__name__}")


def _visit_copy(tacky_copy: TACKYCopy) -> List:
    return [AssemblyMov(_visit_value(tacky_copy.src), _visit_value(tacky_copy.dst))]


def _visit_label(tacky_label: TACKYLabel) -> List:
    return [AssemblyLabel(tacky_label.identifier)]


def _visit_instruction(tacky_instr: TACKYInstruction) -> List:
    if isinstance(tacky_instr, TACKYUnaryOp):
        return _visit_unary(tacky_instr)
    elif isinstance(tacky_instr, TACKYReturn):
        return _visit_return(tacky_instr)
    elif isinstance(tacky_instr, TACKYBinaryOp):
        return _visit_binary(tacky_instr)
    elif isinstance(
        tacky_instr,
        (TACKYJumpIfZero, TACKYJumpIfNotZero, TACKYJump),
    ):
        return _visit_jump(tacky_instr)
    elif isinstance(tacky_instr, TACKYCopy):
        return _visit_copy(tacky_instr)
    elif isinstance(tacky_instr, TACKYLabel):
        return _visit_label(tacky_instr)
    else:
        raise NotImplementedError(f"No visit logic in _visit_instruction: {type(tacky_instr).__name__}")


def _visit_function(tacky_func: TACKYFunction) -> AssemblyFunction:
    instructions: List = []
    oa = OffsetAllocator()
    for instr in tacky_func.instructions:
        instructions.extend(_visit_instruction(instr))

    return AssemblyFunction(tacky_func.identifier, instructions, oa)


def _visit_program(tacky_prog: TACKYProgram) -> AssemblyProgram:
    func = _visit_function(tacky_prog.function_definition)
    func = _replace_pseudoregisters(func)
    func = _instruction_fixup(func)
    return AssemblyProgram(func)


SrcOperand: TypeAlias = AssemblyImmediate | AssemblyRegister | AssemblyStack
DstOperand: TypeAlias = AssemblyRegister | AssemblyStack


def _stackify(operand: Operand, offsets: OffsetAllocator) -> Operand:
    if isinstance(operand, AssemblyPseudoRegister):
        return AssemblyStack(offsets[operand.identifier])
    return operand


def _replace_pseudoregisters(assembly_func: AssemblyFunction) -> AssemblyFunction:
    new_instructions: List[Any] = []

    for instruction in assembly_func.instructions:
        match instruction:
            case AssemblyMov(e, r):
                new_instructions.append(
                    AssemblyMov(
                        _stackify(e, assembly_func.offsets),
                        _stackify(r, assembly_func.offsets),
                    )
                )

            case AssemblyUnary(op, o):
                if isinstance(o, AssemblyPseudoRegister):
                    new_instructions.append(AssemblyUnary(op, _stackify(o, assembly_func.offsets)))
                else:
                    new_instructions.append(instruction)

            case AssemblyBinaryOp(op, o1, o2):
                new_instructions.append(
                    AssemblyBinaryOp(
                        op,
                        _stackify(o1, assembly_func.offsets),
                        _stackify(o2, assembly_func.offsets),
                    )
                )

            case AssemblyIDiv(o1):
                if isinstance(o1, AssemblyPseudoRegister):
                    new_instructions.append(AssemblyIDiv(_stackify(o1, assembly_func.offsets)))
                else:
                    new_instructions.append(instruction)

            case AssemblyCompare(o1, o2):
                if isinstance(o1, AssemblyPseudoRegister) and isinstance(o2, AssemblyPseudoRegister):
                    new_instructions.append(
                        AssemblyMov(
                            _stackify(o1, assembly_func.offsets),
                            AssemblyRegister.R10,
                        )
                    )
                    new_instructions.append(AssemblyCompare(AssemblyRegister.R10, _stackify(o2, assembly_func.offsets)))
                elif isinstance(o2, AssemblyImmediate):
                    new_instructions.append(
                        AssemblyMov(
                            AssemblyImmediate(o2.value),
                            AssemblyRegister.R11,
                        )
                    )
                    new_instructions.append(AssemblyCompare(AssemblyRegister.R11, _stackify(o1, assembly_func.offsets)))

            case AssemblySetConditionCode(cond_code, operand):
                new_instructions.append(AssemblySetConditionCode(cond_code, _stackify(operand, assembly_func.offsets)))

            case _:
                new_instructions.append(instruction)

    return AssemblyFunction(assembly_func.name, new_instructions, assembly_func.offsets)


def _is_mem(x: Operand) -> bool:
    return isinstance(x, AssemblyStack)


def _is_imm(x: Operand) -> bool:
    return isinstance(x, AssemblyImmediate)


def _instruction_fixup(assembly_func: AssemblyFunction) -> AssemblyFunction:
    frame_size = ((assembly_func.offsets.max_offset + 15) // 16) * 16  # Need to keep the stack frame a multiple of 16
    new_instructions: List[Any] = [AssemblyAllocateStack(frame_size)]

    for instruction in assembly_func.instructions:
        match instruction:

            case AssemblyMov(AssemblyStack(src_off), AssemblyStack(dst_off)):
                new_instructions.append(AssemblyMov(AssemblyStack(src_off), AssemblyRegister.R10))
                new_instructions.append(AssemblyMov(AssemblyRegister.R10, AssemblyStack(dst_off)))

            case AssemblyIDiv(op) if _is_imm(op):
                new_instructions.append(AssemblyMov(cast(AssemblyImmediate, op), AssemblyRegister.R10))
                new_instructions.append(AssemblyIDiv(AssemblyRegister.R10))

            case AssemblyBinaryOp(op, src, dst):
                if op == AssemblyBinaryOpType.MULTIPLY:
                    if _is_mem(dst):
                        dst_off = cast(AssemblyStack, dst).offset
                        new_instructions.append(AssemblyMov(AssemblyStack(dst_off), AssemblyRegister.R11))

                        fixed_src: Operand
                        if _is_mem(src):
                            new_instructions.append(AssemblyMov(cast(AssemblyStack, src), AssemblyRegister.R10))
                            fixed_src = AssemblyRegister.R10
                        else:
                            fixed_src = src

                        new_instructions.append(
                            AssemblyBinaryOp(
                                AssemblyBinaryOpType.MULTIPLY,
                                fixed_src,
                                AssemblyRegister.R11,
                            )
                        )
                        new_instructions.append(AssemblyMov(AssemblyRegister.R11, AssemblyStack(dst_off)))

                    else:
                        if _is_mem(src) and _is_mem(dst):
                            new_instructions.append(AssemblyMov(cast(AssemblyStack, src), AssemblyRegister.R10))
                            new_instructions.append(
                                AssemblyBinaryOp(
                                    AssemblyBinaryOpType.MULTIPLY,
                                    AssemblyRegister.R10,
                                    dst,
                                )
                            )
                        else:
                            new_instructions.append(instruction)

                elif op == AssemblyBinaryOpType.ADD or op == AssemblyBinaryOpType.SUBTRACT:
                    if _is_mem(src) and _is_mem(dst):
                        new_instructions.append(AssemblyMov(cast(AssemblyStack, src), AssemblyRegister.R10))
                        new_instructions.append(AssemblyBinaryOp(op, AssemblyRegister.R10, dst))
                    else:
                        new_instructions.append(instruction)

                else:
                    if _is_mem(src) and _is_mem(dst):
                        new_instructions.append(AssemblyMov(cast(AssemblyStack, src), AssemblyRegister.R10))
                        new_instructions.append(AssemblyBinaryOp(op, AssemblyRegister.R10, dst))
                    else:
                        new_instructions.append(instruction)

            case _:
                new_instructions.append(instruction)

    return AssemblyFunction(assembly_func.name, new_instructions, assembly_func.offsets)


def convert_TACKY_to_assembly(tacky_prog: TACKYProgram) -> AssemblyProgram:
    return _visit_program(tacky_prog)
