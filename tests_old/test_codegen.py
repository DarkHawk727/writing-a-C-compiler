import unittest

from backend.tacky2asm import convert_AST_to_assembly
from frontend.parser import Constant, Function, Identifier, Program, Return


class CodeGenTest(unittest.TestCase):
    def test_normal(self):
        ast = Program(
            main_func=Function(
                name=Identifier(name="main"),
                body=Return(return_val=Constant(val=100)),
            )
        )

        instructions = convert_AST_to_assembly(ast)

        self.assertListEqual(
            [
                "_main:",
                "\tpushq  %rbp",
                "\tmovq  %rsp, %rbp",
                "\tmovl  $100, %eax",
                "\tpopq  %rbp",
                "\tretq",
            ],
            instructions,
        )

    def test_normal_2(self):
        ast = Program(
            main_func=Function(
                name=Identifier(name="main"),
                body=Return(return_val=Constant(val=1)),
            )
        )

        instructions = convert_AST_to_assembly(ast)

        self.assertListEqual(
            [
                "_main:",
                "\tpushq  %rbp",
                "\tmovq  %rsp, %rbp",
                "\tmovl  $1, %eax",
                "\tpopq  %rbp",
                "\tretq",
            ],
            instructions,
        )
