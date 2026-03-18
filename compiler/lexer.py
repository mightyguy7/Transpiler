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

        self.keywords = {"int","void" ,"return","if","else","while","for","do"}
        self.operators = {"+", "-", "*", "/", "=",">","<","%"}

    def advance(self):
        self.pos += 1
        if self.pos >= len(self.code):
            self.current = None
        else:
            self.current = self.code[self.pos]

    def tokenize(self):
        tokens = []
        
        while self.current is not None:

            if self.current == "[":
                tokens.append(Token("LBRACKET", "["))
                self.advance()
                continue

            if self.current == "]":
                tokens.append(Token("RBRACKET", "]"))
                self.advance()
                continue

            if self.current == "&" and self.pos+1 < len(self.code) and self.code[self.pos+1] == "&":
                tokens.append(Token("LOGIC", "&&"))
                self.advance()
                self.advance()
                continue

            if self.current == "|" and self.pos+1 < len(self.code) and self.code[self.pos+1] == "|":
                tokens.append(Token("LOGIC", "||"))
                self.advance()
                self.advance()
                continue

            if self.current == "!":
                tokens.append(Token("LOGIC", "!"))
                self.advance()
                continue

            if self.current == "#":
                while self.current and self.current != "\n":
                    self.advance()
                self.advance()
                continue

            if self.current.isspace():
                self.advance()
                continue

            # numbers
            if self.current.isdigit():
                num = ""
                while self.current and self.current.isdigit():
                    num += self.current
                    self.advance()

                tokens.append(Token("NUMBER", num))
                continue

            if self.current == "/" and self.pos + 1 < len(self.code) and self.code[self.pos+1] == "/":
                self.advance()
                self.advance()

                comment = ""

                while self.current and self.current != "\n":
                    comment += self.current
                    self.advance()

                tokens.append(Token("COMMENT", comment.strip()))
                continue

            if self.current == "/" and self.pos + 1 < len(self.code) and self.code[self.pos+1] == "*":
                self.advance()
                self.advance()

                comment = ""

                while self.current and not (self.current == "*" and self.pos + 1 < len(self.code) and self.code[self.pos+1] == "/"):
                    comment += self.current
                    self.advance()

                self.advance()
                self.advance()

                tokens.append(Token("COMMENT", comment.strip()))
                continue

            # identifiers / keywords
            if self.current.isalpha() or self.current == "_":
                word = ""

                while self.current and (self.current.isalnum() or self.current == "_"):
                    word += self.current
                    self.advance()

                if word in self.keywords:
                    tokens.append(Token("KEYWORD", word))
                else:
                    tokens.append(Token("IDENTIFIER", word))

                continue

            # two-character operators
            if self.pos + 1 < len(self.code):
                two = self.current + self.code[self.pos + 1]

                if two in {"<=", ">=", "==", "!=","+=", "-=", "*=", "/=", "%="}:
                    tokens.append(Token("OPERATOR", two))
                    self.advance()
                    self.advance()
                    continue

            # increment operator
            if self.current == "+" and self.pos + 1 < len(self.code) and self.code[self.pos + 1] == "+":
                tokens.append(Token("INCREMENT", "++"))
                self.advance()
                self.advance()
                continue

            # operators
            if self.current in self.operators:
                tokens.append(Token("OPERATOR", self.current))
                self.advance()
                continue

            if self.current == ";":
                tokens.append(Token("SEMICOLON", ";"))
                self.advance()
                continue

            # string literals
            if self.current == '"':
                self.advance()
                string = ""

                while self.current and self.current != '"':
                    # if self.current == "\\":
                    #     self.advance()
                    #     if self.current == "n":
                    #         string += "\\n"
                    #     elif self.current == "t":
                    #         string += "\\t"
                    #     else:
                    #         string += "\\" + self.current
                    #     self.advance()
                    #     continue
                    string+=self.current;
                    self.advance()

                self.advance()  # skip closing quote
                tokens.append(Token("STRING", string))
                continue

            if self.current == "(":
                tokens.append(Token("LPAREN", "("))
                self.advance()
                continue

            if self.current == ")":
                tokens.append(Token("RPAREN", ")"))
                self.advance()
                continue

            if self.current == "{":
                tokens.append(Token("LBRACE", "{"))
                self.advance()
                continue

            if self.current == "}":
                tokens.append(Token("RBRACE", "}"))
                self.advance()
                continue

            if self.current == ",":
                tokens.append(Token("COMMA", ","))
                self.advance()
                continue
            if self.current == "&":
                tokens.append(Token("AMP", "&"))
                self.advance()
                continue
            raise Exception("Invalid character: " + self.current)

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
        if self.pos >= len(self.tokens):
            self.current = None
        else:
            self.current = self.tokens[self.pos]

    def factor(self):

        token = self.current
        if token.type == "SEMICOLON":
            return None
        if token.type == "NUMBER":
            self.advance()
            return ASTNode("NUMBER", token.value)
        if token.type == "LOGIC" and token.value == "!":
            self.advance()
            expr = self.factor()
            return ASTNode("NOT", "!", expr)
        if token.type == "LPAREN":
            self.advance()
            expr = self.expression()
            self.advance()
            return expr
        
        if token.type == "IDENTIFIER":
            name = token.value
            self.advance()
            node = ASTNode("IDENTIFIER", name)
            

            # function call
            if self.current and self.current.type == "LPAREN":
                self.advance()
                args = []
                while self.current and self.current.type != "RPAREN":
                    if self.current.type == "COMMA":
                        self.advance()
                        continue
                    args.append(self.expression())
                self.advance()
                node = ASTNode("CALL", name, children=args)

            # ⭐ array access: arr[i]
            elif self.current and self.current.type == "LBRACKET":
                self.advance()  # skip [
                index = self.expression()
                self.advance()  # skip ]
                node = ASTNode("ARRAY_ACCESS", name, left=index)

            # postfix increment
            if self.current and self.current.type == "INCREMENT":
                self.advance()
                node = ASTNode("INC", name)

            return node

        raise Exception(f"Unexpected token in expression: {token.type} {token.value}")
    
    def expression(self):

        left = self.factor()

        while self.current and (self.current.type == "OPERATOR" or self.current.type == "LOGIC"):
            op = self.current
            self.advance()

            right = self.factor()

            if op.value == "+":
                left = ASTNode("ADD", "+", left, right)
            elif op.value == "-":
                left = ASTNode("SUB", "-", left, right)
            elif op.value == "/":
                left = ASTNode("DIV", "/", left, right)
            elif op.value == "*":
                left = ASTNode("MUL", "*", left, right)
            elif op.value == "%":
                left = ASTNode("MOD", "%", left, right)
            elif op.value == "&&":
                left = ASTNode("AND", "&&", left, right)

            elif op.value == "||":
                left = ASTNode("OR", "||", left, right)
            elif op.value == "+=":
                left = ASTNode("PLUSEQ", "+=", left, right)

            elif op.value == "-=":
                left = ASTNode("MINUSEQ", "-=", left, right)

            elif op.value == "*=":
                left = ASTNode("MULEQ", "*=", left, right)

            elif op.value == "/=":
                left = ASTNode("DIVEQ", "/=", left, right)

            elif op.value == "%=":
                left = ASTNode("MODEQ", "%=", left, right)
        return left

    def parse(self):

        statements = []

        while self.current is not None:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            
        return ASTNode("PROGRAM", children=statements)
    
    def statement(self):

        if self.current.type == "KEYWORD" and self.current.value == "if":
            return self.if_statement()

        if self.current.type == "KEYWORD" and self.current.value == "while":
            return self.while_statement()

        if self.current.type == "KEYWORD" and self.current.value == "for":
            return self.for_statement()

        if self.current.type == "KEYWORD" and self.current.value == "do":
            return self.do_while_statement()
        # array index assignment: arr[i] = expr
        if self.current.type == "IDENTIFIER" and self.peek() and self.peek().type == "LBRACKET":
            return self.array_assignment()
        # handle bare blocks { ... }
        if self.current.type == "LBRACE":
            stmts = self.block()
            return ASTNode("BLOCK", children=stmts)
        if self.current.type == "IDENTIFIER" and self.current.value == "printf":
            return self.printf_statement()
        if self.current.type == "IDENTIFIER" and self.current.value == "scanf":
            return self.scanf_statement()
        if self.current.type == "KEYWORD" and self.current.value in {"int","void"}:
            if self.peek() and self.peek().type == "IDENTIFIER":
                if self.tokens[self.pos+2].type == "LPAREN":
                    return self.function_definition()
            return self.declaration()
        if self.current.type == "KEYWORD" and self.current.value == "int":
            return self.declaration()
        
        # if self.current.type == "IDENTIFIER" and self.peek() and self.peek().type == "INCREMENT":
        #     return self.increment()
        # if self.current.type == "IDENTIFIER":
        #     return self.assignment()
        if self.current.type == "IDENTIFIER" and self.peek() and self.peek().type == "INCREMENT":
            name = self.current.value
            self.advance()  # skip identifier
            self.advance()  # skip ++
            if self.current and self.current.type == "SEMICOLON":
                self.advance()
            return ASTNode("INC", name)

        if self.current.type == "IDENTIFIER" and self.peek() and self.peek().type == "OPERATOR":
            return self.assignment()
        if self.current.type == "KEYWORD" and self.current.value == "return":
            return self.return_statement()
        if self.current.type == "IDENTIFIER" and self.current.value == "scanf":
            return self.scanf_statement()
        if self.current.type == "COMMENT":
            text = self.current.value
            self.advance()
            return ASTNode("COMMENT", text)
        raise Exception(f"Unknown statement: {self.current.type} {self.current.value}")
    
    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    # def increment(self):
    #     var = self.current.value
    #     self.advance()  # identifier
    #     self.advance()  # ++
    #     # self.advance()
    #     if self.current and self.current.type == "SEMICOLON":
    #         self.advance()
    #     return ASTNode("INC", var)
    
    # def assignment(self):

    #     var = self.current
    #     self.advance()

    #     self.advance()  # skip =

    #     expr = self.expression()

    #     if self.current.type == "SEMICOLON":
    #         self.advance()

    #     return ASTNode("ASSIGN", var.value, expr)
    def array_assignment(self):
        name = self.current.value
        self.advance()  # skip identifier
        self.advance()  # skip [
        index = self.expression()
        self.advance()  # skip ]
        self.advance()  # skip =
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

        if op.value == "=":
            return ASTNode("ASSIGN", var, expr)

        elif op.value == "+=":
            return ASTNode("PLUSEQ", "+=", ASTNode("IDENTIFIER", var), expr)

        elif op.value == "-=":
            return ASTNode("MINUSEQ", "-=", ASTNode("IDENTIFIER", var), expr)

        elif op.value == "*=":
            return ASTNode("MULEQ", "*=", ASTNode("IDENTIFIER", var), expr)

        elif op.value == "/=":
            return ASTNode("DIVEQ", "/=", ASTNode("IDENTIFIER", var), expr)

        elif op.value == "%=":
            return ASTNode("MODEQ", "%=", ASTNode("IDENTIFIER", var), expr)

        else:
            raise Exception("Invalid assignment operator")
    def printf_statement(self):
        self.advance()  # printf
        self.advance()  # (

        fmt = self.current
        self.advance()

        args = []

        while self.current and self.current.type != "RPAREN":

            if self.current.type == "COMMA":
                self.advance()
                args.append(self.factor())
            else:
                self.advance()

        self.advance()  # )

        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        return ASTNode("PRINTF", fmt.value, children=args)

    def declaration(self):
        self.advance()  # skip 'int'
        variables = []

        while self.current and self.current.type == "IDENTIFIER":
            var = self.current.value
            self.advance()

            # Array declaration: int arr[5]  or  int arr[] = {1,2,3}
            if self.current and self.current.type == "LBRACKET":
                self.advance()  # skip [
                size = None
                if self.current and self.current.type != "RBRACKET":
                    size = self.current.value
                    self.advance()
                self.advance()  # skip ]

                # int arr[] = {1, 2, 3}
                if self.current and self.current.value == "=":
                    self.advance()  # skip =
                    self.advance()  # skip {
                    elements = []
                    while self.current and self.current.type != "RBRACE":
                        if self.current.type == "COMMA":
                            self.advance()
                            continue
                        elements.append(self.expression())
                    self.advance()  # skip }
                    variables.append(ASTNode("ARRAY_INIT", var, children=elements))
                else:
                    # int arr[5]  →  arr = [0] * 5
                    variables.append(ASTNode("ARRAY_DECL", var, children=[ASTNode("NUMBER", size)]))

            # Normal int a = 5
            elif self.current and self.current.value == "=":
                self.advance()
                expr = self.expression()
                variables.append(ASTNode("ASSIGN", var, expr))

            else:
                variables.append(ASTNode("DECL", var))

            if self.current and self.current.type == "COMMA":
                self.advance()
                continue
            break

        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        return ASTNode("DECLLIST", children=variables)
    
    def if_statement(self):

        self.advance()  # skip if
        self.advance()  # skip (
        left = self.factor()
        op = self.current
        self.advance()
        right = self.factor()
        condition = ASTNode("COMPARE", op.value, left, right)
        self.advance()  # skip )
        self.advance()  # skip {

        if_body = []

        while self.current and self.current.type != "RBRACE":
            stmt = self.statement()
            if stmt:
                if_body.append(stmt)

        self.advance()  # skip }

        else_body = []

        # check for else
        if self.current and self.current.type == "KEYWORD" and self.current.value == "else":

            self.advance()  # skip else
            self.advance()  # skip {

            while self.current and self.current.type != "RBRACE":
                stmt = self.statement()
                if stmt:
                    else_body.append(stmt)

            self.advance()  # skip }

        return ASTNode("IF", left=condition, children=[if_body, else_body])
    
    def while_statement(self):

        self.advance()  # skip while
        self.advance()  # skip (

        left = self.factor()
        op = self.current
        self.advance()
        right = self.factor()

        condition = ASTNode("COMPARE", op.value, left, right)

        self.advance()  # skip )

        body = self.block()   # ⭐ FIX

        return ASTNode("WHILE", left=condition, children=body)
    
    def do_while_statement(self):

        self.advance()  # skip do

        body = self.block()

        self.advance()  # skip while
        self.advance()  # skip (

        left = self.factor()
        op = self.current
        self.advance()
        right = self.factor()

        condition = ASTNode("COMPARE", op.value, left, right)

        self.advance()  # skip )
        self.advance()  # skip ;

        return ASTNode("DO_WHILE", left=condition, children=body)
    
    def for_statement(self):

        self.advance()  # skip for
        self.advance()  # skip (

        init = self.declaration()

        # condition
        left = self.factor()
        op = self.current
        self.advance()
        right = self.factor()

        condition = ASTNode("COMPARE", op.value, left, right)

        self.advance()  # skip ;

        # increment (general expression)
        increment = self.expression()

        self.advance()  # skip )

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
    
    def scanf_statement(self):
        self.advance()  # scanf
        self.advance()  # (
        fmt = self.current
        self.advance()
        vars = []
        while self.current and self.current.type != "RPAREN":

            if self.current.type == "COMMA":
                self.advance()
                continue
            if self.current.type == "AMP":
                self.advance()
                vars.append(self.current.value)
                self.advance()
                continue

            self.advance()
        self.advance()  # )

        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        return ASTNode("SCANF", fmt.value, children=vars)
    def function_definition(self):

        self.advance()  # skip return type (int)

        name = self.current.value
        self.advance()

        self.advance()  # (

        params = []

        while self.current and self.current.type != "RPAREN":

            if self.current.type == "KEYWORD":  # parameter type
                self.advance()
                params.append(self.current.value)
                self.advance()

            elif self.current.type == "COMMA":
                self.advance()

        self.advance()  # )

        body = self.block()

        return ASTNode("FUNCTION", name, children=[params, body])
    
    def return_statement(self):
        self.advance()  # skip return
        expr = None
        if self.current and self.current.type != "SEMICOLON":
            expr = self.expression()

        if self.current and self.current.type == "SEMICOLON":
            self.advance()

        return ASTNode("RETURN", left=expr)
class CodeGenerator:

    def generate(self, node):
        if node is None:
            return ""
        
        if node.type == "PROGRAM":

            lines = []

            has_main = False

            for child in node.children:
                code = self.generate(child)
                lines.append(code)

                if child.type == "FUNCTION" and child.value == "main":
                    has_main = True

            if has_main:
                lines.append("\nmain()")

            return "\n".join(lines)

        if node.type == "NUMBER":
            return node.value

        if node.type == "IDENTIFIER":
            return node.value

        if node.type == "ADD":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} + {right}"

        if node.type == "ASSIGN":
            expr = self.generate(node.left)
            return f"{node.value} = {expr}"

        if node.type == "PRINT":
            return f'print("{node.value}")'
        
        if node.type == "COMPARE":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} {node.value} {right}"
        
        if node.type == "IF":

            condition = self.generate(node.left)

            if_body = node.children[0]
            else_body = node.children[1]

            lines = [f"if {condition}:"]

            for stmt in if_body:
                generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first


            if else_body:
                lines.append("else:")

                for stmt in else_body:
                    generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first


            return "\n".join(lines)
        
        if node.type == "SUB":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} - {right}"

        if node.type == "MUL":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} * {right}"

        if node.type == "DIV":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} / {right}"

        if node.type == "MOD":
            left = self.generate(node.left)
            right = self.generate(node.right)
            return f"{left} % {right}"
        
        if node.type == "WHILE":
            condition = self.generate(node.left)

            lines = [f"while {condition}:"]

            for stmt in node.children:
                generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first


            return "\n".join(lines)
        if node.type == "DO_WHILE":

            condition = self.generate(node.left)

            lines = ["while True:"]

            for stmt in node.children:
                generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first


            lines.append(f"    if not ({condition}):")
            lines.append("        break")

            return "\n".join(lines)
        
        if node.type == "FOR":
            init = node.children[0]       # DECLLIST or ASSIGN
            condition = node.children[1]  # COMPARE node
            increment = node.children[2]  # INC or expression
            body = node.children[3]

            # Extract start value
            if init.type == "DECLLIST" and init.children:
                assign = init.children[0]  # ASSIGN node like i = 0
                var = assign.value
                start = self.generate(assign.left)
            else:
                var = init.value
                start = "0"

            # Extract stop value from condition (i < n  or  i <= n)
            stop = self.generate(condition.right)
            if condition.value == "<=":
                stop = f"{stop} + 1"

            # Extract step from increment
            if increment.type == "INC":
                step = None  # default step 1, no need to write it
            elif increment.type == "PLUSEQ":
                step = self.generate(increment.right)
            elif increment.type == "MINUSEQ":
                step = f"-{self.generate(increment.right)}"
            else:
                step = None

            if step:
                range_str = f"range({start}, {stop}, {step})"
            else:
                range_str = f"range({start}, {stop})"

            lines = [f"for {var} in {range_str}:"]
            for stmt in body:
                generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first


            return "\n".join(lines)
            
        if node.type == "INC":
                return f"{node.value} += 1"
        
        if node.type == "PRINTF":

            args = [self.generate(a) for a in node.children]

            if args:
                return f'print({", ".join(args)})'
            else:
                return f'print("{node.value}")'
            
        if node.type == "SCANF":

            vars = node.children

            if len(vars) == 1:
                return f"{vars[0]} = int(input())"

            else:
                return f"{', '.join(vars)} = map(int, input().split())"
        if node.type == "DECL":
            return f"{node.value} = 0"
        if node.type == "DECLLIST":
            lines = []
            plain_vars = []
            
            for child in node.children:
                if child.type == "DECL":
                    plain_vars.append(child.value)
                else:
                    # if we have collected plain vars, emit them first
                    if plain_vars:
                        lines.append(" = ".join(plain_vars) + " = 0")
                        plain_vars = []
                    lines.append(self.generate(child))
            
            # emit any remaining plain vars
            if plain_vars:
                lines.append(" = ".join(plain_vars) + " = 0")
            
            return "\n".join(lines)
        
        # if node.type == "FUNCTION":

        #     name = node.value
        #     params = node.children[0]
        #     body = node.children[1]

        #     lines = [f"def {name}({', '.join(params)}):"]

        #     if not body:
        #         lines.append("    pass")
        #     else:
        #         for stmt in body:
        #             lines.append("    " + self.generate(stmt))

        #     return "\n".join(lines)
        if node.type == "FUNCTION":
            name = node.value
            params = node.children[0]
            body = node.children[1]

            lines = [f"def {name}({', '.join(params)}):"]

            for stmt in body:
                # ⭐ handle multi-line statements (like DECLLIST with multiple vars)
                generated = self.generate(stmt)
                for line in generated.split("\n"):
                    lines.append("    " + line)  # ⭐ indent EVERY line, not just first

            return "\n".join(lines)

        if node.type == "RETURN":
            if node.left:
                return f"return {self.generate(node.left)}"
            return "return"
        
        if node.type == "CALL":
            args = [self.generate(a) for a in node.children]

            return f"{node.value}({', '.join(args)})"
        if node.type == "COMMENT":
            lines = node.value.split("\n")
            return "\n".join("# " + l.strip() for l in lines)
        if node.type=="AND":
            return f"{self.generate(node.left)} and {self.generate(node.right)}"
        if node.type=="OR":
            return f"{self.generate(node.left)} or {self.generate(node.right)}"
        if node.type=="NOT":
            return f"not{self.generate(node.left)}" 
        if node.type == "PLUSEQ":
            return f"{self.generate(node.left)} += {self.generate(node.right)}"

        if node.type == "MINUSEQ":
            return f"{self.generate(node.left)} -= {self.generate(node.right)}"

        if node.type == "MULEQ":
            return f"{self.generate(node.left)} *= {self.generate(node.right)}"

        if node.type == "DIVEQ":
            return f"{self.generate(node.left)} /= {self.generate(node.right)}"

        if node.type == "MODEQ":
            return f"{self.generate(node.left)} %= {self.generate(node.right)}"
        if node.type == "ARRAY_DECL":
            # int arr[5]  →  arr = [0] * 5
            size=node.children[0].value if node.children else "0"
            return f"{node.value} = [0] * {size}"

        if node.type == "ARRAY_INIT":
            # int arr[] = {1,2,3}  →  arr = [1, 2, 3]
            elements = [self.generate(e) for e in node.children]
            return f"{node.value} = [{', '.join(elements)}]"

        if node.type == "ARRAY_ACCESS":
            # arr[i]  →  arr[i]
            index = self.generate(node.left)
            return f"{node.value}[{index}]"

        if node.type == "ARRAY_ASSIGN":
            # arr[i] = expr  →  arr[i] = expr
            index = self.generate(node.left)
            value = self.generate(node.right)
            return f"{node.value}[{index}] = {value}"
        if node.type == "BLOCK":
            return "\n".join(self.generate(s) for s in node.children)
        
# code = """
# #include<stdio.h>
# for(int i=0;i<n;i++)
# {
#     //printf("aa");
#     /*while(j<n)
#     {
#     //j++;
#     }

# }
# do {*/
# i++;
# }
# while(i<2);
# int s = 10;
# printf("%d%d\n",s,s);
# int a,b,c;
# scanf("%d%d", &a,&b);
# int add(int a, int b,int c){
#     return a || b;
    
# }
# for(int i=0;i<n;i+=1){
# j*=2;
# }
# int arr[5];
# int arr[]={1,2,3};
# arr[i+1]=arr[i]*2;
# """
# lexer = Lexer(code)
# tokens = lexer.tokenize()
# for t in tokens:
#     print(t.type, t.value)
# parser = Parser(tokens)
# ast = parser.parse()

# generator = CodeGenerator()
# python_code = generator.generate(ast)

# print(python_code)
