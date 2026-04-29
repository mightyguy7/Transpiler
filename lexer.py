class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"{self.type}:{self.value}"


class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.current = code[0] if code else None
        self.keywords = {
            "int", "void", "return", "if", "else", "while", "for", "do",
            "float", "double", "char", "long", "long long", "break", "continue"
        }
        self.operators = {"+", "-", "*", "/", "=", ">", "<", "%"}

    def advance(self):
        self.pos += 1
        self.current = self.code[self.pos] if self.pos < len(self.code) else None

    def tokenize(self):
        tokens = []

        while self.current is not None:

            if self.current == "[":
                tokens.append(Token("LBRACKET", "[")); self.advance(); continue
            if self.current == "]":
                tokens.append(Token("RBRACKET", "]")); self.advance(); continue

            # two-char operators
            if self.pos + 1 < len(self.code):
                two = self.current + self.code[self.pos + 1]
                if two in {"<=", ">=", "==", "!=", "+=", "-=", "*=", "/=", "%=", "&&", "||"}:
                    tokens.append(Token("OPERATOR", two))
                    self.advance(); self.advance(); continue

            # ++ / --
            if self.current == "+" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "+":
                tokens.append(Token("INCREMENT", "++")); self.advance(); self.advance(); continue
            if self.current == "-" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "-":
                tokens.append(Token("DECREMENT", "--")); self.advance(); self.advance(); continue

            # single !
            if self.current == "!":
                tokens.append(Token("LOGIC", "!")); self.advance(); continue

            # preprocessor directive — skip whole line
            if self.current == "#":
                while self.current and self.current != "\n":
                    self.advance()
                if self.current:
                    self.advance()
                continue

            if self.current.isspace():
                self.advance(); continue

            # numbers
            if self.current.isdigit():
                num = ""
                while self.current and self.current.isdigit():
                    num += self.current; self.advance()
                if self.current == ".":
                    num += self.current; self.advance()
                    while self.current and self.current.isdigit():
                        num += self.current; self.advance()
                if self.current and self.current in ("f", "F"):
                    self.advance()
                tokens.append(Token("NUMBER", num)); continue

            # float starting with dot like .5
            if self.current == "." and self.pos + 1 < len(self.code) and self.code[self.pos + 1].isdigit():
                num = "."
                self.advance()
                while self.current and self.current.isdigit():
                    num += self.current; self.advance()
                tokens.append(Token("NUMBER", num)); continue

            # // comment
            if self.current == "/" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "/":
                self.advance(); self.advance()
                comment = ""
                while self.current and self.current != "\n":
                    comment += self.current; self.advance()
                tokens.append(Token("COMMENT", comment.strip())); continue

            # /* comment */
            if self.current == "/" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "*":
                self.advance(); self.advance()
                comment = ""
                while self.current and not (
                    self.current == "*" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "/"
                ):
                    comment += self.current; self.advance()
                self.advance(); self.advance()
                tokens.append(Token("COMMENT", comment.strip())); continue

            # identifiers / keywords
            if self.current.isalpha() or self.current == "_":
                word = ""
                while self.current and (self.current.isalnum() or self.current == "_"):
                    word += self.current; self.advance()

                # handle "long long" as a single keyword token
                if word == "long":
                    temp_pos = self.pos
                    while temp_pos < len(self.code) and self.code[temp_pos].isspace():
                        temp_pos += 1
                    if self.code[temp_pos:temp_pos + 4] == "long":
                        next_end = temp_pos + 4
                        if next_end >= len(self.code) or not self.code[next_end].isalnum():
                            self.pos = next_end
                            self.current = self.code[self.pos] if self.pos < len(self.code) else None
                            word = "long long"

                ttype = "KEYWORD" if word in self.keywords else "IDENTIFIER"
                tokens.append(Token(ttype, word)); continue

            # single-char operators
            if self.current in self.operators:
                tokens.append(Token("OPERATOR", self.current)); self.advance(); continue
            if self.current == ";":  tokens.append(Token("SEMICOLON", ";")); self.advance(); continue
            if self.current == "(":  tokens.append(Token("LPAREN",   "(")); self.advance(); continue
            if self.current == ")":  tokens.append(Token("RPAREN",   ")")); self.advance(); continue
            if self.current == "{":  tokens.append(Token("LBRACE",   "{")); self.advance(); continue
            if self.current == "}":  tokens.append(Token("RBRACE",   "}")); self.advance(); continue
            if self.current == ",":  tokens.append(Token("COMMA",    ",")); self.advance(); continue
            if self.current == "&":  tokens.append(Token("AMP",      "&")); self.advance(); continue

            # string literals
            if self.current == '"':
                self.advance()
                string = ""
                while self.current and self.current != '"':
                    if self.current == '\\' and self.pos + 1 < len(self.code):
                        string += self.current
                        self.advance()
                        string += self.current
                        self.advance()
                    else:
                        string += self.current; self.advance()
                self.advance()
                tokens.append(Token("STRING", string)); continue

            # char literals 'a'
            if self.current == "'":
                self.advance()
                char = ""
                while self.current and self.current != "'":
                    char += self.current; self.advance()
                self.advance()
                tokens.append(Token("CHAR", char)); continue

            raise Exception("Invalid character: " + repr(self.current))

        return tokens


class ASTNode:
    def __init__(self, type, value=None, left=None, right=None, children=None):
        self.type = type
        self.value = value
        self.left = left
        self.right = right
        self.children = children or []

    def __repr__(self):
        return f"{self.type}({self.value})"


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0] if tokens else None

    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    # ── Expression parsing (proper precedence) ────────────────────────────────

    def parse_primary(self):
        """Highest precedence: literals, identifiers, calls, array access, grouped expr."""
        token = self.current

        if token is None:
            raise Exception("Unexpected end of input in expression")

        if token.type == "NUMBER":
            self.advance()
            return ASTNode("NUMBER", token.value)

        if token.type == "CHAR":
            self.advance()
            return ASTNode("CHAR", token.value)

        if token.type == "STRING":
            self.advance()
            return ASTNode("STRING", token.value)

        if token.type == "LOGIC" and token.value == "!":
            self.advance()
            expr = self.parse_primary()
            return ASTNode("NOT", "!", expr)

        # Unary minus
        if token.type == "OPERATOR" and token.value == "-":
            self.advance()
            expr = self.parse_primary()
            return ASTNode("SUB", "-", ASTNode("NUMBER", "0"), expr)

        if token.type == "LPAREN":
            self.advance()          # skip (
            expr = self.expression()
            if self.current and self.current.type == "RPAREN":
                self.advance()      # skip )
            return expr

        if token.type == "IDENTIFIER":
            name = token.value
            self.advance()
            node = ASTNode("IDENTIFIER", name)

            if self.current and self.current.type == "LPAREN":
                # function call
                self.advance()      # skip (
                args = []
                while self.current and self.current.type != "RPAREN":
                    if self.current.type == "COMMA":
                        self.advance(); continue
                    args.append(self.expression())
                if self.current and self.current.type == "RPAREN":
                    self.advance()  # skip )
                node = ASTNode("CALL", name, children=args)

            elif self.current and self.current.type == "LBRACKET":
                # array access arr[i]
                self.advance()      # skip [
                index = self.expression()
                if self.current and self.current.type == "RBRACKET":
                    self.advance()  # skip ]
                node = ASTNode("ARRAY_ACCESS", name, left=index)

            # postfix ++ / --
            if self.current and self.current.type == "INCREMENT":
                self.advance()
                node = ASTNode("POST_INC", name, left=node)
            elif self.current and self.current.type == "DECREMENT":
                self.advance()
                node = ASTNode("POST_DEC", name, left=node)

            return node

        if token.type == "INCREMENT":
            # prefix ++var
            self.advance()
            if self.current and self.current.type == "IDENTIFIER":
                name = self.current.value
                self.advance()
                return ASTNode("INC", name)
            raise Exception("Expected identifier after ++")

        if token.type == "DECREMENT":
            # prefix --var
            self.advance()
            if self.current and self.current.type == "IDENTIFIER":
                name = self.current.value
                self.advance()
                return ASTNode("DEC", name)
            raise Exception("Expected identifier after --")

        raise Exception(f"Unexpected token in expression: {token.type} '{token.value}'")

    def parse_multiplicative(self):
        """* / %"""
        left = self.parse_primary()
        while self.current and self.current.type == "OPERATOR" and self.current.value in ("*", "/", "%"):
            op = self.current.value
            self.advance()
            right = self.parse_primary()
            type_map = {"*": "MUL", "/": "DIV", "%": "MOD"}
            left = ASTNode(type_map[op], op, left, right)
        return left

    def parse_additive(self):
        """+ -"""
        left = self.parse_multiplicative()
        while self.current and self.current.type == "OPERATOR" and self.current.value in ("+", "-"):
            op = self.current.value
            self.advance()
            right = self.parse_multiplicative()
            type_map = {"+": "ADD", "-": "SUB"}
            left = ASTNode(type_map[op], op, left, right)
        return left

    def parse_relational(self):
        """< > <= >="""
        left = self.parse_additive()
        while (self.current and self.current.type == "OPERATOR"
               and self.current.value in ("<", ">", "<=", ">=")):
            op = self.current.value
            self.advance()
            right = self.parse_additive()
            left = ASTNode("COMPARE", op, left, right)
        return left

    def parse_equality(self):
        """== !="""
        left = self.parse_relational()
        while (self.current and self.current.type == "OPERATOR"
               and self.current.value in ("==", "!=")):
            op = self.current.value
            self.advance()
            right = self.parse_relational()
            left = ASTNode("COMPARE", op, left, right)
        return left

    def parse_logical_and(self):
        """&&"""
        left = self.parse_equality()
        while self.current and self.current.type == "OPERATOR" and self.current.value == "&&":
            self.advance()
            right = self.parse_equality()
            left = ASTNode("AND", "&&", left, right)
        return left

    def parse_logical_or(self):
        """||"""
        left = self.parse_logical_and()
        while self.current and self.current.type == "OPERATOR" and self.current.value == "||":
            self.advance()
            right = self.parse_logical_and()
            left = ASTNode("OR", "||", left, right)
        return left

    def expression(self):
        """Full expression with assignment operators handled at statement level."""
        return self.parse_logical_or()

    # ── Statement parsing ─────────────────────────────────────────────────────

    def parse(self):
        statements = []
        while self.current is not None:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        return ASTNode("PROGRAM", children=statements)

    def statement(self):

        if self.current is None:
            return None

        # Skip stray semicolons
        if self.current.type == "SEMICOLON":
            self.advance()
            return None

        # --- comment ---
        if self.current.type == "COMMENT":
            text = self.current.value
            self.advance()
            return ASTNode("COMMENT", text)

        # --- if ---
        if self.current.type == "KEYWORD" and self.current.value == "if":
            return self.if_statement()

        # --- while ---
        if self.current.type == "KEYWORD" and self.current.value == "while":
            return self.while_statement()

        # --- for ---
        if self.current.type == "KEYWORD" and self.current.value == "for":
            return self.for_statement()

        # --- do-while ---
        if self.current.type == "KEYWORD" and self.current.value == "do":
            return self.do_while_statement()

        # --- break / continue ---
        if self.current.type == "KEYWORD" and self.current.value == "break":
            self.advance()
            if self.current and self.current.type == "SEMICOLON": self.advance()
            return ASTNode("BREAK")

        if self.current.type == "KEYWORD" and self.current.value == "continue":
            self.advance()
            if self.current and self.current.type == "SEMICOLON": self.advance()
            return ASTNode("CONTINUE")

        # --- bare block { ... } ---
        if self.current.type == "LBRACE":
            stmts = self.block()
            return ASTNode("BLOCK", children=stmts)

        # --- printf ---
        if self.current.type == "IDENTIFIER" and self.current.value == "printf":
            return self.printf_statement()

        # --- scanf ---
        if self.current.type == "IDENTIFIER" and self.current.value == "scanf":
            return self.scanf_statement()

        # --- type keyword → declaration or function definition ---
        if self.current.type == "KEYWORD" and self.current.value in {
            "int", "void", "float", "double", "char", "long", "long long"
        }:
            # function definition: type name ( ...
            if (self.peek() and self.peek().type == "IDENTIFIER"
                    and self.pos + 2 < len(self.tokens)
                    and self.tokens[self.pos + 2].type == "LPAREN"):
                return self.function_definition()
            return self.declaration()

        # --- return ---
        if self.current.type == "KEYWORD" and self.current.value == "return":
            return self.return_statement()

        # --- array assignment  arr[i] = expr ---
        if (self.current.type == "IDENTIFIER"
                and self.peek() and self.peek().type == "LBRACKET"):
            return self.array_assignment()

        # --- prefix ++ identifier ---
        if self.current.type == "INCREMENT":
            self.advance()
            name = self.current.value
            self.advance()
            if self.current and self.current.type == "SEMICOLON": self.advance()
            return ASTNode("INC", name)

        # --- prefix -- identifier ---
        if self.current.type == "DECREMENT":
            self.advance()
            name = self.current.value
            self.advance()
            if self.current and self.current.type == "SEMICOLON": self.advance()
            return ASTNode("DEC", name)

        # --- identifier-based statements ---
        if self.current.type == "IDENTIFIER":
            name = self.current.value

            # postfix ++/-- as statement
            if self.peek() and self.peek().type == "INCREMENT":
                self.advance(); self.advance()
                if self.current and self.current.type == "SEMICOLON": self.advance()
                return ASTNode("INC", name)

            if self.peek() and self.peek().type == "DECREMENT":
                self.advance(); self.advance()
                if self.current and self.current.type == "SEMICOLON": self.advance()
                return ASTNode("DEC", name)

            # assignment / compound-assignment
            if self.peek() and self.peek().type == "OPERATOR" and self.peek().value in (
                "=", "+=", "-=", "*=", "/=", "%="
            ):
                return self.assignment()

            # standalone function call
            if self.peek() and self.peek().type == "LPAREN":
                expr = self.expression()
                if self.current and self.current.type == "SEMICOLON": self.advance()
                return expr

        raise Exception(f"Unknown statement: {self.current.type} '{self.current.value}'")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def array_assignment(self):
        name = self.current.value
        self.advance()  # identifier
        self.advance()  # [
        index = self.expression()
        if self.current and self.current.type == "RBRACKET":
            self.advance()          # ]
        if self.current and self.current.type == "OPERATOR" and self.current.value == "=":
            self.advance()          # =
        value = self.expression()
        if self.current and self.current.type == "SEMICOLON":
            self.advance()
        return ASTNode("ARRAY_ASSIGN", name, left=index, right=value)

    def assignment(self):
        var = self.current.value
        self.advance()
        op = self.current
        self.advance()
        expr = self.expression()
        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        op_map = {
            "=":  ("ASSIGN",   None),
            "+=": ("PLUSEQ",   "+="),
            "-=": ("MINUSEQ",  "-="),
            "*=": ("MULEQ",    "*="),
            "/=": ("DIVEQ",    "/="),
            "%=": ("MODEQ",    "%="),
        }
        if op.value not in op_map:
            raise Exception(f"Invalid assignment operator: {op.value}")

        node_type, node_val = op_map[op.value]
        if node_type == "ASSIGN":
            return ASTNode("ASSIGN", var, expr)
        return ASTNode(node_type, node_val, ASTNode("IDENTIFIER", var), expr)

    def printf_statement(self):
        self.advance()  # printf
        if self.current and self.current.type == "LPAREN":
            self.advance()  # (
        fmt = self.current.value
        self.advance()  # format string token
        args = []
        while self.current and self.current.type != "RPAREN":
            if self.current.type == "COMMA":
                self.advance()
                if self.current and self.current.type != "RPAREN":
                    args.append(self.expression())
            else:
                self.advance()
        if self.current and self.current.type == "RPAREN":
            self.advance()  # )
        if self.current and self.current.type == "SEMICOLON":
            self.advance()
        return ASTNode("PRINTF", fmt, children=args)

    def scanf_statement(self):
        self.advance()  # scanf
        if self.current and self.current.type == "LPAREN":
            self.advance()  # (
        fmt = self.current.value if self.current else ""
        self.advance()  # format string
        vars_ = []
        while self.current and self.current.type != "RPAREN":
            if self.current.type == "COMMA":
                self.advance(); continue
            if self.current.type == "AMP":
                self.advance()
                if self.current and self.current.type == "IDENTIFIER":
                    vars_.append(ASTNode("IDENTIFIER", self.current.value))
                    self.advance()
                continue
            self.advance()
        if self.current and self.current.type == "RPAREN":
            self.advance()  # )
        if self.current and self.current.type == "SEMICOLON":
            self.advance()
        return ASTNode("SCANF", fmt, children=vars_)

    def declaration(self):
        type_kw = self.current.value
        self.advance()
        variables = []

        while self.current and self.current.type == "IDENTIFIER":
            var = self.current.value
            self.advance()

            if self.current and self.current.type == "LBRACKET":
                self.advance()  # [
                size = None
                if self.current and self.current.type != "RBRACKET":
                    size = self.current.value
                    self.advance()
                self.advance()  # ]

                if self.current and self.current.value == "=":
                    self.advance()  # =
                    self.advance()  # {
                    elements = []
                    while self.current and self.current.type != "RBRACE":
                        if self.current.type == "COMMA":
                            self.advance(); continue
                        elements.append(self.expression())
                    self.advance()  # }
                    variables.append(ASTNode("ARRAY_INIT", var, children=elements))
                else:
                    variables.append(ASTNode("ARRAY_DECL", var,
                                             children=[ASTNode("NUMBER", size or "0")]))

            elif self.current and self.current.value == "=":
                self.advance()
                expr = self.expression()
                variables.append(ASTNode("ASSIGN", var, expr))

            else:
                variables.append(ASTNode("DECL", var, left=ASTNode("TYPE", type_kw)))

            if self.current and self.current.type == "COMMA":
                self.advance(); continue
            break

        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        return ASTNode("DECLLIST", value=type_kw, children=variables)

    def if_statement(self):
        self.advance()  # skip 'if'
        if self.current and self.current.type == "LPAREN":
            self.advance()          # skip (
        condition = self.expression()
        if self.current and self.current.type == "RPAREN":
            self.advance()          # skip )

        if_body = []
        if self.current and self.current.type == "LBRACE":
            if_body = self.block()
        else:
            stmt = self.statement()
            if stmt:
                if_body.append(stmt)

        else_body = []
        if self.current and self.current.type == "KEYWORD" and self.current.value == "else":
            self.advance()  # skip 'else'
            if self.current and self.current.type == "LBRACE":
                else_body = self.block()
            else:
                stmt = self.statement()
                if stmt:
                    else_body.append(stmt)

        return ASTNode("IF", left=condition, children=[if_body, else_body])

    def while_statement(self):
        self.advance()  # skip 'while'
        if self.current and self.current.type == "LPAREN":
            self.advance()          # skip (
        condition = self.expression()
        if self.current and self.current.type == "RPAREN":
            self.advance()          # skip )
        body = self.block()
        return ASTNode("WHILE", left=condition, children=body)

    def do_while_statement(self):
        self.advance()  # skip 'do'
        body = self.block()
        self.advance()  # skip 'while'
        if self.current and self.current.type == "LPAREN":
            self.advance()          # skip (
        condition = self.expression()
        if self.current and self.current.type == "RPAREN":
            self.advance()          # skip )
        if self.current and self.current.type == "SEMICOLON":
            self.advance()
        return ASTNode("DO_WHILE", left=condition, children=body)

    def for_statement(self):
        self.advance()  # skip 'for'
        self.advance()  # skip (

        init = self.declaration()

        # condition expression
        condition = self.expression()
        if self.current and self.current.type == "SEMICOLON":
            self.advance()  # skip ;

        increment = self.expression()

        if self.current and self.current.type == "RPAREN":
            self.advance()          # skip )

        body = self.block()
        return ASTNode("FOR", children=[init, condition, increment, body])

    def block(self):
        self.advance()  # skip {
        statements = []
        while self.current and self.current.type != "RBRACE":
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        self.advance()  # skip }
        return statements

    def function_definition(self):
        self.advance()  # skip return type
        name = self.current.value
        self.advance()
        self.advance()  # skip (
        params = []
        while self.current and self.current.type != "RPAREN":
            if self.current.type == "COMMA":
                self.advance(); continue
            if self.current.type == "KEYWORD":
                self.advance()  # skip type
                if self.current and self.current.type == "IDENTIFIER":
                    param_name = self.current.value
                    self.advance()
                    if self.current and self.current.type == "LBRACKET":
                        self.advance()
                        if self.current and self.current.type != "RBRACKET":
                            self.advance()
                        self.advance()
                    params.append(param_name)
                continue
            self.advance()
        self.advance()  # skip )
        body = self.block()
        return ASTNode("FUNCTION", name, children=[params, body])

    def return_statement(self):
        self.advance()  # skip 'return'
        expr = None
        if self.current and self.current.type != "SEMICOLON":
            expr = self.expression()
        if self.current and self.current.type == "SEMICOLON":
            self.advance()
        return ASTNode("RETURN", left=expr)


class CodeGenerator:

    TYPE_DEFAULTS = {
        "int":       "0",
        "float":     "0.0",
        "double":    "0.0",
        "char":      "''",
        "long":      "0",
        "long long": "0",
        "void":      "None",
    }

    def generate(self, node):
        if node is None:
            return ""

        if node.type == "PROGRAM":
            lines = []
            has_main = False
            for child in node.children:
                code = self.generate(child)
                if code:
                    lines.append(code)
                if child.type == "FUNCTION" and child.value == "main":
                    has_main = True
            if has_main:
                lines.append("\nmain()")
            return "\n".join(lines)

        if node.type == "NUMBER":
            return node.value

        if node.type == "CHAR":
            return f"'{node.value}'"

        if node.type == "STRING":
            return f'"{node.value}"'

        if node.type == "IDENTIFIER":
            return node.value

        if node.type == "ASSIGN":
            expr = self.generate(node.left)
            return f"{node.value} = {expr}"

        if node.type == "ADD":
            return f"{self.generate(node.left)} + {self.generate(node.right)}"
        if node.type == "SUB":
            return f"{self.generate(node.left)} - {self.generate(node.right)}"
        if node.type == "MUL":
            return f"{self.generate(node.left)} * {self.generate(node.right)}"
        if node.type == "DIV":
            return f"{self.generate(node.left)} // {self.generate(node.right)}"
        if node.type == "MOD":
            return f"{self.generate(node.left)} % {self.generate(node.right)}"

        if node.type == "AND":
            return f"{self.generate(node.left)} and {self.generate(node.right)}"
        if node.type == "OR":
            return f"{self.generate(node.left)} or {self.generate(node.right)}"
        if node.type == "NOT":
            return f"not {self.generate(node.left)}"

        if node.type == "COMPARE":
            op = node.value
            # C's != maps directly, all others map directly
            return f"{self.generate(node.left)} {op} {self.generate(node.right)}"

        if node.type == "PLUSEQ":
            return f"{self.generate(node.left)} += {self.generate(node.right)}"
        if node.type == "MINUSEQ":
            return f"{self.generate(node.left)} -= {self.generate(node.right)}"
        if node.type == "MULEQ":
            return f"{self.generate(node.left)} *= {self.generate(node.right)}"
        if node.type == "DIVEQ":
            return f"{self.generate(node.left)} //= {self.generate(node.right)}"
        if node.type == "MODEQ":
            return f"{self.generate(node.left)} %= {self.generate(node.right)}"

        if node.type == "INC":
            return f"{node.value} += 1"
        if node.type == "DEC":
            return f"{node.value} -= 1"

        if node.type in ("POST_INC",):
            return f"{node.left.value if node.left else node.value} += 1"
        if node.type in ("POST_DEC",):
            return f"{node.left.value if node.left else node.value} -= 1"

        if node.type == "DECL":
            type_kw = node.left.value if node.left else "int"
            default = self.TYPE_DEFAULTS.get(type_kw, "0")
            return f"{node.value} = {default}"

        if node.type == "DECLLIST":
            lines = []
            plain_vars = []
            type_kw = node.value

            for child in node.children:
                if child.type == "DECL":
                    plain_vars.append(child.value)
                else:
                    if plain_vars:
                        default = self.TYPE_DEFAULTS.get(type_kw, "0")
                        lines.append(" = ".join(plain_vars) + f" = {default}")
                        plain_vars = []
                    lines.append(self.generate(child))

            if plain_vars:
                default = self.TYPE_DEFAULTS.get(type_kw, "0")
                lines.append(" = ".join(plain_vars) + f" = {default}")

            return "\n".join(lines)

        if node.type == "IF":
            condition = self.generate(node.left)
            if_body   = node.children[0]
            else_body = node.children[1]

            lines = [f"if {condition}:"]
            for stmt in if_body:
                for line in self.generate(stmt).split("\n"):
                    lines.append("    " + line)
            if else_body:
                lines.append("else:")
                for stmt in else_body:
                    for line in self.generate(stmt).split("\n"):
                        lines.append("    " + line)
            return "\n".join(lines)

        if node.type == "WHILE":
            condition = self.generate(node.left)
            lines = [f"while {condition}:"]
            for stmt in node.children:
                for line in self.generate(stmt).split("\n"):
                    lines.append("    " + line)
            return "\n".join(lines)

        if node.type == "DO_WHILE":
            condition = self.generate(node.left)
            lines = ["while True:"]
            for stmt in node.children:
                for line in self.generate(stmt).split("\n"):
                    lines.append("    " + line)
            lines.append(f"    if not ({condition}):")
            lines.append("        break")
            return "\n".join(lines)

        if node.type == "FOR":
            init      = node.children[0]
            condition = node.children[1]
            increment = node.children[2]
            body      = node.children[3]

            # Try to use Python range() for simple numeric for-loops
            try:
                if init.type == "DECLLIST" and init.children:
                    assign = init.children[0]
                    var    = assign.value
                    start  = self.generate(assign.left)
                elif init.type == "ASSIGN":
                    var   = init.value
                    start = self.generate(init.left)
                else:
                    raise ValueError("complex init")

                if condition.type != "COMPARE":
                    raise ValueError("non-compare condition")

                cond_op = condition.value
                stop    = self.generate(condition.right)

                if increment.type == "INC":
                    step = None
                elif increment.type == "DEC":
                    step = "-1"
                elif increment.type == "PLUSEQ":
                    step = self.generate(increment.right)
                elif increment.type == "MINUSEQ":
                    step = f"-{self.generate(increment.right)}"
                else:
                    raise ValueError("complex increment")

                if cond_op == "<=":
                    stop = f"{stop} + 1"
                elif cond_op == "<":
                    pass
                else:
                    raise ValueError("unsupported loop condition")

                range_str = f"range({start}, {stop}, {step})" if step else f"range({start}, {stop})"
                lines = [f"for {var} in {range_str}:"]
                for stmt in body:
                    for line in self.generate(stmt).split("\n"):
                        lines.append("    " + line)
                return "\n".join(lines)
            except (ValueError, AttributeError):
                # Fall back to while-loop translation
                init_code = self.generate(init)
                cond_code = self.generate(condition)
                incr_code = self.generate(increment)
                lines = [init_code, f"while {cond_code}:"]
                for stmt in body:
                    for line in self.generate(stmt).split("\n"):
                        lines.append("    " + line)
                lines.append(f"    {incr_code}")
                return "\n".join(lines)

        if node.type == "FUNCTION":
            name   = node.value
            params = node.children[0]
            body   = node.children[1]
            lines  = [f"def {name}({', '.join(params)}):"]
            for stmt in body:
                code = self.generate(stmt)
                if code:
                    for line in code.split("\n"):
                        lines.append("    " + line)
            if len(lines) == 1:
                lines.append("    pass")
            return "\n".join(lines)

        if node.type == "RETURN":
            if node.left:
                return f"return {self.generate(node.left)}"
            return "return"

        if node.type == "CALL":
            args = [self.generate(a) for a in node.children]
            return f"{node.value}({', '.join(args)})"

        if node.type == "PRINTF":
            import re
            fmt  = node.value
            args = [self.generate(a) for a in node.children]

            # Unescape the format string for Python
            clean = fmt.replace('\\n', '\n').replace('\\t', '\t')

            specifiers = re.findall(r'%(?:lld|ld|lf|[dfsc])', clean)
            clean = re.sub(r'%(?:lld|ld|lf|[dfsc])', '{}', clean)

            # Strip trailing newline (print adds it)
            has_newline = clean.endswith('\n')
            if has_newline:
                clean = clean[:-1]

            if args and specifiers:
                result = clean
                for arg in args:
                    result = result.replace('{}', '{' + arg + '}', 1)
                if has_newline:
                    return f'print(f"{result}")'
                else:
                    return f'print(f"{result}", end="")'
            elif args:
                if has_newline:
                    return f'print({", ".join(args)})'
                else:
                    return f'print({", ".join(args)}, end="")'
            else:
                if has_newline:
                    return f'print("{clean}")'
                else:
                    return f'print("{clean}", end="")'

        if node.type == "SCANF":
            import re
            vars_      = node.children
            fmt        = node.value
            specifiers = re.findall(r'%(?:lld|ld|lf|[dfiucs])', fmt)

            lines = []
            if len(vars_) == 1:
                var  = self.generate(vars_[0])
                spec = specifiers[0] if specifiers else "%d"
                if spec in ("%f", "%lf"):
                    lines.append(f"{var} = float(input())")
                elif spec == "%c":
                    lines.append(f"{var} = input()[0]")
                elif spec == "%s":
                    lines.append(f"{var} = input()")
                else:
                    lines.append(f"{var} = int(input())")
            else:
                # multiple vars on one line: a, b = map(int, input().split())
                var_names = [self.generate(v) for v in vars_]
                spec = specifiers[0] if specifiers else "%d"
                if spec in ("%f", "%lf"):
                    lines.append(f"{', '.join(var_names)} = map(float, input().split())")
                else:
                    lines.append(f"{', '.join(var_names)} = map(int, input().split())")
            return "\n".join(lines)

        if node.type == "ARRAY_DECL":
            size = node.children[0].value if node.children else "0"
            return f"{node.value} = [0] * {size}"

        if node.type == "ARRAY_INIT":
            elements = [self.generate(e) for e in node.children]
            return f"{node.value} = [{', '.join(elements)}]"

        if node.type == "ARRAY_ACCESS":
            return f"{node.value}[{self.generate(node.left)}]"

        if node.type == "ARRAY_ASSIGN":
            return f"{node.value}[{self.generate(node.left)}] = {self.generate(node.right)}"

        if node.type == "BLOCK":
            lines = [self.generate(s) for s in node.children if s]
            return "\n".join(lines)

        if node.type == "COMMENT":
            return "\n".join("# " + l.strip() for l in node.value.split("\n"))

        if node.type == "BREAK":
            return "break"

        if node.type == "CONTINUE":
            return "continue"

        # fallback — unknown node, silently skip
        return f"# [unhandled: {node.type}]"