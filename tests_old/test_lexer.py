import unittest

from frontend.lexer import lex


class LexerTest(unittest.TestCase):
    def test_basic(self):
        prog = """
        int main(void) {
            return 1;
        }
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "1", ";", "}"])

    def test_multi_digit(self):
        prog = """
        int main(void) 
        {
            return 69;
        }
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "69", ";", "}"])

    def test_allman_braces(self):
        prog = """
        int 
        main
        (
        void
        ) 
        {
        return
        0
        ;
        }
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "0", ";", "}"])

    def test_no_newlines(self):
        prog = """
        int main(void) {return 69;}
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "69", ";", "}"])

    def test_return_zero(self):
        prog = """
        int main(void) 
        {
            return 0;
        }
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "0", ";", "}"])

    def test_return_2(self):
        prog = """
        int main(void) 
        {
            return 2;
        }
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "2", ";", "}"])

    def test_spaces(self):
        prog = """
          int   main(   void )   {    return 69 ; } 
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "69", ";", "}"])

    def test_tabs(self):
        prog = """
        int    main    (    void)    {       return  0    ;    }    
        """
        self.assertListEqual(lex(prog), ["int", "main", "(", "void", ")", "{", "return", "0", ";", "}"])

    def test_at_sign(self):
        prog = """
        int main(void) {
            return 0@1;
        }
        """
        with self.assertRaises(ValueError):
            lex(prog)

    def test_backslash(self):
        prog = """
        \\
        """
        with self.assertRaises(ValueError):
            lex(prog)

    def test_backtick(self):
        prog = """
        `
        """
        with self.assertRaises(ValueError):
            lex(prog)

    def test_invalid_identifier(self):
        prog = """
        int main(void) {
            return 1foo;
        }
        """
        with self.assertRaises(ValueError):
            lex(prog)

    def test_invalid_identifier_2(self):
        prog = """
        int main(void) {
            return @b;
        }
        """
        with self.assertRaises(ValueError):
            lex(prog)


if __name__ == "__main__":
    unittest.main()
