#!/opt/homebrew/bin/python3.10
import argparse
import os

from backend.codegen import emit_assembly
from backend.tacky2asm import convert_TACKY_to_assembly
from frontend.lexer import lex
from frontend.parser import parse_program
from middle.tacky import convert_AST_to_TACKY
from utils.viz import pretty_print_tree, ast_to_mermaid, pretty_tacky


def render(obj, viz_mode: str) -> str:
    """
    Render an intermediate object either as pretty text or Mermaid.
    - Mermaid is most useful for parse/TACKY/assembly IR trees.
    - For non-tree outputs (like token lists), we fall back to str().
    """
    if viz_mode == "mermaid":
        try:
            return ast_to_mermaid(obj)
        except Exception:
            # If it's not a tree-like structure, just print it plainly.
            return str(obj)
    else:
        # pretty
        try:
            return pretty_print_tree(obj)
        except Exception:
            return str(obj)


def print_section(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body)


def main():
    parser = argparse.ArgumentParser(description="Compiler with stage selection & visualization")
    parser.add_argument("file", help="Input file to process")
    parser.add_argument(
        "--stage",
        choices=["lex", "parse", "tacky", "codegen", "compile", "all"],
        default="all",
        help="Select the compiler stage to run (default: all)",
    )
    parser.add_argument(
        "--viz",
        choices=["pretty", "mermaid"],
        default="pretty",
        help="Choose visualization for tree-like stages (default: pretty)",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        return

    with open(args.file, "r") as f:
        program = f.read()

    # Common pipeline pieces (so we don't recompute)
    tokens = None
    ast = None
    tacky = None
    asm_ir = None

    def run_lex():
        nonlocal tokens
        if tokens is None:
            tokens = list(lex(program))
        # Mermaid doesn't make sense for tokens; just print them line-by-line.
        body = "\n".join(map(str, tokens))
        print_section("LEX", body)

    def run_parse():
        nonlocal ast, tokens
        if ast is None:
            if tokens is None:
                tokens = list(lex(program))
            ast = parse_program(tokens)
        print_section("PARSE", render(ast, args.viz))

    def run_tacky():
        nonlocal tacky, ast, tokens
        if tacky is None:
            if ast is None:
                if tokens is None:
                    tokens = list(lex(program))
                ast = parse_program(tokens)
            tacky = convert_AST_to_TACKY(ast)
        print_section("TACKY", pretty_tacky(tacky))

    def run_codegen():
        nonlocal asm_ir, tacky, ast, tokens
        if asm_ir is None:
            if tacky is None:
                if ast is None:
                    if tokens is None:
                        tokens = list(lex(program))
                    ast = parse_program(tokens)
                tacky = convert_AST_to_TACKY(ast)
            asm_ir = convert_TACKY_to_assembly(tacky)
        print_section("CODEGEN (Assembly IR)", render(asm_ir, args.viz))

    def run_compile():
        nonlocal asm_ir
        if asm_ir is None:
            run_codegen()  # ensures asm_ir exists (and prints it)
        out_path = f"{args.file[:-2]}.s"
        with open(out_path, "w") as out:
            for instruction in emit_assembly(asm_ir):
                out.write(instruction + "\n")
        print_section("COMPILE", f"Wrote assembly to: {out_path}")

    # Dispatch
    if args.stage == "lex":
        run_lex()
    elif args.stage == "parse":
        run_parse()
    elif args.stage == "tacky":
        run_tacky()
    elif args.stage == "codegen":
        run_codegen()
    elif args.stage == "compile":
        # Keep prior behavior but now also prints upstream stages' output by default via run_codegen()
        run_compile()
    elif args.stage == "all":
        # Default: print everything in order; compile last.
        run_lex()
        run_parse()
        run_tacky()
        run_codegen()
        # Do not auto-write the .s file in 'all' unless you want that.
        # If you *do* want it, uncomment the next line:
        # run_compile()
    else:
        raise AssertionError("Unreachable")


if __name__ == "__main__":
    main()
