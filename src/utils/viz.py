from __future__ import annotations

import html
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


GRAPHICAL_FORMATS = {"svg", "html", "dot"}

_NODE_WIDTH = 220
_X_GAP = 36
_Y_GAP = 96
_PADDING = 14
_LINE_HEIGHT = 17
_HEADER_HEIGHT = 28


@dataclass
class VizNode:
    node_id: str
    title: str
    fields: list[str] = field(default_factory=list)
    children: list[tuple[str, VizNode]] = field(default_factory=list)
    x: float = 0
    y: float = 0
    width: float = _NODE_WIDTH
    height: float = 0
    subtree_width: float = 0


def is_namedtuple_instance(x: Any) -> bool:
    return isinstance(x, tuple) and hasattr(x, "_fields")


def is_primitive(x: Any) -> bool:
    return isinstance(x, (str, int, float, bool)) or x is None


def is_leaf_value(x: Any) -> bool:
    return is_primitive(x) or isinstance(x, Enum)


def op_symbol(x: Any) -> str | None:
    if not isinstance(x, Enum):
        return None

    symbols = {
        "ADD": "+",
        "SUBTRACT": "-",
        "MULTIPLY": "*",
        "DIVIDE": "/",
        "REMAINDER": "%",
        "BITWISE_AND": "&",
        "BITWISE_OR": "|",
        "BITWISE_XOR": "^",
        "L_SHIFT": "<<",
        "R_SHIFT": ">>",
        "LOGICAL_AND": "&&",
        "LOGICAL_OR": "||",
        "EQUAL": "==",
        "NOT_EQUAL": "!=",
        "LESS_THAN": "<",
        "LESS_THAN_OR_EQUAL": "<=",
        "GREATER_THAN": ">",
        "GREATER_THAN_OR_EQUAL": ">=",
        "COMPLEMENT": "~",
        "NEGATION": "-",
        "NOT": "!",
    }
    return symbols.get(x.name)


def _value_label(x: Any) -> str:
    sym = op_symbol(x)
    if sym is not None:
        return repr(sym)
    if isinstance(x, Enum):
        return x.name
    return repr(x)


def _wrap_line(text: str, width: int = 28) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False) or [text]


def _field_lines(fields: Iterable[str]) -> list[str]:
    lines: list[str] = []
    for field_text in fields:
        lines.extend(_wrap_line(field_text))
    return lines


def _new_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"n{counter[0]}"


def _build_tree(root: Any, counter: list[int] | None = None) -> VizNode:
    if counter is None:
        counter = [0]

    node_id = _new_id(counter)

    if isinstance(root, list):
        node = VizNode(node_id=node_id, title=f"list[{len(root)}]")
        if not root:
            node.fields.append("empty")
        for i, item in enumerate(root):
            node.children.append((f"[{i}]", _build_tree(item, counter)))
        return node

    if is_namedtuple_instance(root):
        node = VizNode(node_id=node_id, title=root.__class__.__name__)
        for field_name in root._fields:
            value = getattr(root, field_name)
            if is_leaf_value(value):
                node.fields.append(f"{field_name} = {_value_label(value)}")
            elif isinstance(value, list):
                if value:
                    node.children.append((field_name, _build_tree(value, counter)))
                else:
                    node.fields.append(f"{field_name} = []")
            else:
                node.children.append((field_name, _build_tree(value, counter)))
        return node

    return VizNode(node_id=node_id, title=root.__class__.__name__, fields=[_value_label(root)])


def _measure(node: VizNode) -> float:
    lines = _field_lines(node.fields)
    node.height = _HEADER_HEIGHT + (len(lines) * _LINE_HEIGHT if lines else 0) + _PADDING

    if not node.children:
        node.subtree_width = node.width
        return node.subtree_width

    children_width = sum(_measure(child) for _, child in node.children)
    children_width += _X_GAP * (len(node.children) - 1)
    node.subtree_width = max(node.width, children_width)
    return node.subtree_width


def _place(node: VizNode, left: float, top: float) -> None:
    node.x = left + (node.subtree_width - node.width) / 2
    node.y = top

    child_left = left + max(0, node.subtree_width - _children_width(node)) / 2
    for _, child in node.children:
        _place(child, child_left, top + node.height + _Y_GAP)
        child_left += child.subtree_width + _X_GAP


def _children_width(node: VizNode) -> float:
    if not node.children:
        return 0
    return sum(child.subtree_width for _, child in node.children) + _X_GAP * (
        len(node.children) - 1
    )


def _iter_nodes(node: VizNode) -> Iterable[VizNode]:
    yield node
    for _, child in node.children:
        yield from _iter_nodes(child)


def _svg_text(text: str, x: float, y: float, class_name: str) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="{class_name}">'
        f"{html.escape(text)}</text>"
    )


def ast_to_svg(root: Any) -> str:
    tree = _build_tree(root)
    _measure(tree)
    _place(tree, 24, 24)

    all_nodes = list(_iter_nodes(tree))
    max_x = max(node.x + node.width for node in all_nodes) + 24
    max_y = max(node.y + node.height for node in all_nodes) + 24

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x:.0f}" '
            f'height="{max_y:.0f}" viewBox="0 0 {max_x:.0f} {max_y:.0f}">'
        ),
        "<style>",
        ".edge{fill:none;stroke:#8a94a6;stroke-width:1.4}",
        ".edge-label{font:12px sans-serif;fill:#566174}",
        ".node{fill:#ffffff;stroke:#7f8ea3;stroke-width:1.2}",
        ".header{fill:#edf4ff}",
        ".title{font:600 13px sans-serif;fill:#172033}",
        ".field{font:12px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#263142}",
        "</style>",
    ]

    for parent in all_nodes:
        start_x = parent.x + parent.width / 2
        start_y = parent.y + parent.height
        for label, child in parent.children:
            end_x = child.x + child.width / 2
            end_y = child.y
            mid_y = start_y + (_Y_GAP / 2)
            parts.append(
                f'<path class="edge" d="M {start_x:.1f} {start_y:.1f} '
                f'C {start_x:.1f} {mid_y:.1f}, {end_x:.1f} {mid_y:.1f}, '
                f'{end_x:.1f} {end_y:.1f}"/>'
            )
            parts.append(_svg_text(label, (start_x + end_x) / 2 + 5, mid_y - 6, "edge-label"))

    for node in all_nodes:
        parts.append(
            f'<rect class="node" x="{node.x:.1f}" y="{node.y:.1f}" '
            f'width="{node.width:.1f}" height="{node.height:.1f}" rx="6"/>'
        )
        parts.append(
            f'<path class="header" d="M {node.x:.1f} {node.y + 6:.1f} '
            f'Q {node.x:.1f} {node.y:.1f} {node.x + 6:.1f} {node.y:.1f} '
            f'H {node.x + node.width - 6:.1f} '
            f'Q {node.x + node.width:.1f} {node.y:.1f} '
            f'{node.x + node.width:.1f} {node.y + 6:.1f} '
            f'V {node.y + _HEADER_HEIGHT:.1f} H {node.x:.1f} Z"/>'
        )
        parts.append(_svg_text(node.title, node.x + _PADDING, node.y + 19, "title"))

        y = node.y + _HEADER_HEIGHT + _LINE_HEIGHT
        for line in _field_lines(node.fields):
            parts.append(_svg_text(line, node.x + _PADDING, y, "field"))
            y += _LINE_HEIGHT

    parts.append("</svg>")
    return "\n".join(parts)


def ast_to_html(root: Any, title: str = "AST Visualization") -> str:
    svg = ast_to_svg(root)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{html.escape(title)}</title>",
            "<style>",
            "body{margin:0;background:#f6f8fb;color:#172033;font-family:system-ui,sans-serif}",
            "main{padding:24px}",
            "h1{font-size:18px;font-weight:650;margin:0 0 16px}",
            ".canvas{overflow:auto;background:white;border:1px solid #d8dee9;border-radius:8px;padding:18px}",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            f"<h1>{html.escape(title)}</h1>",
            f'<div class="canvas">{svg}</div>',
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def ast_to_dot(root: Any) -> str:
    tree = _build_tree(root)
    lines = [
        "digraph AST {",
        "  graph [rankdir=TB, bgcolor=\"transparent\", nodesep=0.45, ranksep=0.75];",
        "  node [shape=record, style=\"rounded,filled\", fillcolor=\"#edf4ff\", color=\"#7f8ea3\", fontname=\"Consolas\"];",
        "  edge [color=\"#8a94a6\", fontname=\"Arial\", fontsize=10];",
    ]

    def esc(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("{", "\\{").replace("}", "\\}").replace("|", "\\|")

    for node in _iter_nodes(tree):
        fields = "\\l".join(esc(line) for line in _field_lines(node.fields))
        label = esc(node.title) if not fields else f"{{{esc(node.title)}|{fields}\\l}}"
        lines.append(f'  {node.node_id} [label="{label}"];')
        for edge_label, child in node.children:
            lines.append(f'  {node.node_id} -> {child.node_id} [label="{esc(edge_label)}"];')

    lines.append("}")
    return "\n".join(lines)


def node_label(x: Any) -> str:
    if is_namedtuple_instance(x):
        fields = []
        for field_name in x._fields:
            value = getattr(x, field_name)
            if is_leaf_value(value):
                fields.append(f"{field_name}={_value_label(value)}")
        return x.__class__.__name__ if not fields else x.__class__.__name__ + "\\n" + "\\n".join(fields)
    if is_leaf_value(x):
        return _value_label(x)
    return x.__class__.__name__


def ast_to_mermaid(root: Any) -> str:
    lines = ["graph TD"]
    counter = [0]

    def visit(x: Any) -> str:
        node_id = _new_id(counter)
        label = node_label(x).replace('"', '\\"').replace("\\n", "<br/>")
        lines.append(f'\t{node_id}["{label}"]')

        if is_namedtuple_instance(x):
            for field_name in x._fields:
                value = getattr(x, field_name)
                if is_leaf_value(value):
                    continue
                if isinstance(value, list):
                    hub = _new_id(counter)
                    lines.append(f'\t{hub}["{field_name}[]"]')
                    lines.append(f"\t{node_id} --> {hub}")
                    for i, item in enumerate(value):
                        child = visit(item)
                        lines.append(f"\t{hub} -->|[{i}]| {child}")
                else:
                    child = visit(value)
                    lines.append(f"\t{node_id} -->|{field_name}| {child}")
        elif isinstance(x, list):
            for i, item in enumerate(x):
                child = visit(item)
                lines.append(f"\t{node_id} -->|[{i}]| {child}")
        return node_id

    visit(root)
    return "\n".join(lines)


def write_visualization(root: Any, output_path: str | Path, fmt: str | None = None) -> Path:
    path = Path(output_path)
    selected_format = (fmt or path.suffix.lstrip(".")).lower()

    if selected_format == "svg":
        body = ast_to_svg(root)
    elif selected_format == "html":
        body = ast_to_html(root)
    elif selected_format == "dot":
        body = ast_to_dot(root)
    else:
        raise ValueError(f"Unsupported visualization format: {selected_format!r}")

    path.write_text(body, encoding="utf-8")
    return path
