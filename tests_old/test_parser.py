import unittest
from frontend.parser import Constant, Function, Identifier, Program, Return, parse_program


# Imagine's that input has already be correctly tokenized
class TestParser(unittest.TestCase):
    def test_end_before_expr(self):
        t = ["int", "main", "(", "void", ")", "{", "return"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_extra_junk(self):
        t = ["int", "main", "(", "void", ")", "{", "return", "2", ";", "}", "foo"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_invalid_function_names(self):
        t = ["int", "3", "(", "void", ")", "{", "return", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_keyword_wrong_case(self):
        t = ["int", "main", "(", "void", ")", "{", "RETURN", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_missing_type(self):
        t = ["main", "(", "void", ")", "{", "return", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_misspelled_keyword(self):
        t = ["main", "(", "void", ")", "{", "returns", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_no_semicolon(self):
        t = ["main", "(", "void", ")", "{", "returns", "0", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_not_expression(self):
        t = ["main", "(", "void", ")", "{", "returns", "int", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_space_in_keywords(self):
        t = ["main", "(", "void", ")", "{", "retur", "n", "int", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_switched_parens(self):
        t = ["int", "main", ")", "(", "{", "return", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_unclosed_brace(self):
        t = ["int", "main", "(", "void", ")", "{", "return", "0", ";"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_unclosed_paren(self):
        t = ["int", "main", "(", "{", "return", "0", ";", "}"]
        with self.assertRaises(SyntaxError):
            parse_program(t)

    def test_return_zero(self):
        t = ["int", "main", "(", "void", ")", "{", "return", "0", ";", "}"]
        ast = parse_program(t)
        self.assertEqual(
            ast,
            Program(
                function_definition=Function(
                    name=Identifier(name="main"),
                    body=Return(return_val=Constant(val=0)),
                )
            ),
        )

    def test_multi_digit(self):
        t = ["int", "main", "(", "void", ")", "{", "return", "100", ";", "}"]
        ast = parse_program(t)
        self.assertEqual(
            ast,
            Program(
                function_definition=Function(
                    name=Identifier(name="main"),
                    body=Return(return_val=Constant(val=100)),
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
