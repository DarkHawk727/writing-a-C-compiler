from typing import Any, Dict, List, NamedTuple

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


def is_namedtuple_instance(x: Any) -> bool:
    return isinstance(x, tuple) and hasattr(x, "_fields")


def is_primitive(x: Any) -> bool:
    return isinstance(x, (str, int, float, bool)) or x is None


def node_label(x: Any) -> str:
    if is_namedtuple_instance(x):
        cls = "**" + x.__class__.__name__ + "**"
        prims = [
            f"{f}={repr(getattr(x, f))}"
            for f in x._fields
            if is_primitive(getattr(x, f))
        ]
        return cls if not prims else cls + "\\n" + "\\n".join(prims)
    if is_primitive(x):
        return repr(x)
    return x.__class__.__name__


def ast_to_mermaid(root: Any) -> str:
    lines = ["graph TD"]
    counter = {"i": 0}

    def new_id() -> str:
        counter["i"] += 1
        return f"n{counter['i']}"

    def visit(x: Any) -> str:
        nid = new_id()
        label = node_label(x).replace('"', '\\"')
        label = label.replace("\\n", "<br/>")
        lines.append(f'\t{nid}["{label}"]')

        if is_namedtuple_instance(x):
            for field in x._fields:
                val = getattr(x, field)
                if is_primitive(val):
                    continue
                if isinstance(val, list):
                    hub = new_id()
                    lines.append(f'\t{hub}["{field}[]"]')
                    lines.append(f"\t{nid} --> {hub}")
                    for i, item in enumerate(val):
                        child = visit(item)
                        lines.append(f"\t{hub} -->|[{i}]| {child}")
                else:
                    child = visit(val)
                    lines.append(f"\t{nid} -->|{field}| {child}")
        elif isinstance(x, list):
            for i, item in enumerate(x):
                child = visit(item)
                lines.append(f"\t{nid} -->|[{i}]| {child}")
        return nid

    visit(root)
    return "\n".join(lines)


def pretty_print_tree(root: NamedTuple, indent=0) -> str:
    spacer = " " * (indent + 2)
    if isinstance(root, list):
        if not root:
            return "[]"
        result = "[\n"
        for item in root:
            result += spacer + pretty_print_tree(item, indent + 2) + ",\n"
        result += " " * (indent) + "]"
        return result
    elif isinstance(root, tuple) and hasattr(root, "_fields"):
        result = f"{type(root).__name__}(\n"
        for field in root._fields:
            value = getattr(root, field)
            result += f"{spacer}{field}="
            result += pretty_print_tree(value, indent + 2)
            result += ",\n"
        result += " " * indent + ")"
        return result
    else:
        return repr(root)


def _val(v: TACKYValue) -> str:
    if isinstance(v, TACKYConstant):
        return str(v.value)
    elif isinstance(v, TACKYVariable):
        return v.identifier
    raise TypeError(f"Unknown TACKY value: {v!r}")


def pretty_tacky(obj: TACKYProgram | TACKYFunction, show_return: bool = True) -> str:
    _BINARY_OP_MAP: Dict[TACKYBinaryOpType, str] = {
        TACKYBinaryOpType.ADD: "+",
        TACKYBinaryOpType.SUBTRACT: "-",
        TACKYBinaryOpType.MULTIPLY: "*",
        TACKYBinaryOpType.DIVIDE: "/",
        TACKYBinaryOpType.REMAINDER: "%",
        TACKYBinaryOpType.BITWISE_AND: "&",
        TACKYBinaryOpType.BITWISE_OR: "|",
        TACKYBinaryOpType.BITWISE_XOR: "^",
        TACKYBinaryOpType.L_SHIFT: "<<",
        TACKYBinaryOpType.R_SHIFT: ">>",
        # Note: && and || should not generally appear here if you lowered them to Jumpes
        TACKYBinaryOpType.EQUAL: "==",
        TACKYBinaryOpType.NOT_EQUAL: "!=",
        TACKYBinaryOpType.LESS_THAN: "<",
        TACKYBinaryOpType.LESS_THAN_OR_EQUAL: "<=",
        TACKYBinaryOpType.GREATER_THAN: ">",
        TACKYBinaryOpType.GREATER_THAN_OR_EQUAL: ">=",
    }

    _UNARY_OP_MAP: Dict[TACKYUnaryOpType, str] = {
        TACKYUnaryOpType.COMPLEMENT: "~",
        TACKYUnaryOpType.NEGATION: "-",
        TACKYUnaryOpType.NOT: "!",
    }

    fn = obj.function_definition if isinstance(obj, TACKYProgram) else obj

    lines: List[str] = []
    for instr in fn.instructions:
        if isinstance(instr, TACKYLabel):
            lines.append(f"{instr.identifier}:")
        elif isinstance(instr, TACKYCopy):
            lines.append(f"{_val(instr.dst)} = {_val(instr.src)}")
        elif isinstance(instr, TACKYJump):
            lines.append(f"goto {instr.target}")
        elif isinstance(instr, TACKYJumpIfZero):
            lines.append(f"ifz {_val(instr.condition)} -> {instr.target}")
        elif isinstance(instr, TACKYJumpIfNotZero):
            lines.append(f"ifnz {_val(instr.condition)} -> {instr.target}")
        elif isinstance(instr, TACKYUnaryOp):
            dst = _val(instr.destination)
            src = _val(instr.source)
            lines.append(f"{dst} = {_UNARY_OP_MAP[instr.unary_operator]}{src}")
        elif isinstance(instr, TACKYBinaryOp):
            dst = _val(instr.destination)
            s1 = _val(instr.source_1)
            s2 = _val(instr.source_2)
            op = _BINARY_OP_MAP[instr.binary_operator]
            lines.append(f"{dst} = {s1} {op} {s2}")
        elif isinstance(instr, TACKYReturn) and show_return:
            lines.append(f"return {_val(instr.value)}")
        else:
            # ignore return if show_return=False
            continue

    return "\n".join(lines)
