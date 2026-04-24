from typing import List

from src.backend.assembly_ir import *

CONDITION_CODE_SUFFIXES = {
    AssemblyConditionCode.E: "e",
    AssemblyConditionCode.NE: "ne",
    AssemblyConditionCode.G: "g",
    AssemblyConditionCode.GE: "ge",
    AssemblyConditionCode.L: "l",
    AssemblyConditionCode.LE: "le",
}


def emit_assembly(node: AssemblyProgram | AssemblyFunction) -> List[str]:
    match node:
        case AssemblyProgram(func):
            return emit_assembly(func)

        case AssemblyFunction(name, instructions):
            lines = [
                f"\t.globl _{name}",
                f"_{name}:",
                "\tpushq\t%rbp",
                "\tmovq\t%rsp, %rbp",
            ]
            for instr in instructions:
                lines.extend(emit_assembly(instr))
            return lines

        case AssemblyMov(exp, register):
            return [f"\tmovl\t{emit_assembly(exp)[0]}, {emit_assembly(register)[0]}"]

        case AssemblyRet():
            return ["\tmovq\t%rbp, %rsp", "\tpopq\t%rbp", "\tret"]

        case AssemblyUnary(uop, operand):
            operand_assembly = emit_assembly(operand)[0]
            match uop:
                case AssemblyUnaryOpType.NEGATION:
                    return [f"\tnegl\t{operand_assembly}"]
                case AssemblyUnaryOpType.COMPLEMENT:
                    return [f"\tnotl\t{operand_assembly}"]

        case AssemblyBinaryOp(op, src, dst):
            src_assembly = emit_assembly(src)[0]
            dst_assembly = emit_assembly(dst)[0]
            match op:
                case AssemblyBinaryOpType.ADD:
                    return [f"\taddl\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.SUBTRACT:
                    return [f"\tsubl\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.MULTIPLY:
                    return [f"\timull\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.BITWISE_AND:
                    return [f"\tandl\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.BITWISE_OR:
                    return [f"\torl\t\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.BITWISE_XOR:
                    return [f"\txorl\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.L_SHIFT:
                    return [f"\tsall\t{src_assembly}, {dst_assembly}"]

                case AssemblyBinaryOpType.R_SHIFT:
                    return [f"\tsarl\t{src_assembly}, {dst_assembly}"]

        case AssemblyIDiv(operand):
            return [f"\tidivl\t{emit_assembly(operand)[0]}"]

        case AssemblyCdq():
            return ["\tcdq"]

        case AssemblyAllocateStack(v):
            return [f"\tsubq\t${abs(v)}, %rsp"]

        case AssemblyRegister() as reg:
            if reg == AssemblyRegister.AX:
                return ["%eax"]
            elif reg == AssemblyRegister.R10:
                return ["%r10d"]
            elif reg == AssemblyRegister.R11:
                return ["%r11d"]
            elif reg == AssemblyRegister.DX:
                return ["%edx"]

        case AssemblyStack(offset):
            return [f"{offset}(%rbp)"]

        case AssemblyImmediate(val):
            return [f"${val}"]

        case AssemblyCompare(operand_1, operand_2):
            operand_1_assembly = emit_assembly(operand_1)[0]
            operand_2_assembly = emit_assembly(operand_2)[0]
            return [f"\tcmpl\t{operand_2_assembly}, {operand_1_assembly}"]

        case AssemblyJump(label):
            return [f"\tjmp\t.L{label}"]

        case AssemblyJumpConditionCode(cond_code, label):
            suffix = CONDITION_CODE_SUFFIXES[cond_code]
            return [f"\tj{suffix}\t.L{label}"]

        case AssemblySetConditionCode(cond_code, operand):
            suffix = CONDITION_CODE_SUFFIXES[cond_code]
            operand_assembly = emit_assembly(operand)[0]
            return [f"\tset{suffix}\t{operand_assembly}"]

        case AssemblyLabel(label):
            return [f".L{label}:"]

        case _:
            raise NotImplementedError(f"No emit logic for {node}")
