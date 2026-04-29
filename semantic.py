class SemanticError:
    def __init__(self, level, message):
        self.level = level
        self.message = message

    def __repr__(self):
        return f"[{self.level}] {self.message}"


class SemanticAnalyzer:

    NUMERIC = {"int", "float", "double", "long", "long long", "char"}

    def __init__(self):
        self.scopes = [{}]
        self.functions = {}
        self.issues = []
        self._current_function = None

    # scope

    def _push_scope(self):
        self.scopes.append({})

    def _pop_scope(self):
        scope = self.scopes.pop()
        for name, info in scope.items():
            if not info["used"] and not info.get("error", False):
                self._warn(f"Variable '{name}' declared but never used")

    def _declare(self, name, var_type="unknown"):
        if name in self.scopes[-1]:
            self._error(f"Variable '{name}' already declared in this scope")
            self.scopes[-1][name]["error"] = True
            return

        if self._lookup(name) is not None:
            self._warn(f"Variable '{name}' shadows outer scope variable")

        self.scopes[-1][name] = {
            "type": var_type,
            "used": False,
            "error": False
        }

    def _lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _mark_used(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name]["used"] = True
                return

    # issues

    def _error(self, msg):
        self.issues.append(SemanticError("ERROR", msg))

    def _warn(self, msg):
        self.issues.append(SemanticError("WARNING", msg))

    # Type Inference 

    def _infer_type(self, node):
        if node is None:
            return "unknown"

        if node.type == "NUMBER":
            return "float" if "." in node.value else "int"

        if node.type == "CHAR":
            if len(node.value) > 1:
                self._error(f"Invalid character literal '{node.value}'")
            return "int"   

        if node.type == "STRING":
            return "string"

        if node.type == "IDENTIFIER":
            info = self._lookup(node.value)
            return info["type"] if info else "unknown"

        if node.type == "CALL":
            if node.value in self.functions:
                return self.functions[node.value]["return_type"]
            return "unknown"

        if node.type == "COMPARE":
            return "int"  

        if node.type in ("ADD", "SUB", "MUL", "DIV", "MOD"):
            left = self._infer_type(node.left)
            right = self._infer_type(node.right)

            if left == "string" or right == "string":
                self._error(f"Invalid operation between {left} and {right}")
                return "unknown"

            if "float" in (left, right) or "double" in (left, right):
                return "float"

            return "int"

        return "unknown"

    def _check_assign_types(self, name, var_type, rhs):
        if rhs is None:
            return

        if var_type.endswith("[]"):
            return

        rhs_type = self._infer_type(rhs)

        if rhs_type == "string" and var_type in self.NUMERIC:
            self._error(f"Cannot assign string to {var_type} '{name}'")

        if var_type == "string" and rhs_type in self.NUMERIC:
            self._error(f"Cannot assign {rhs_type} to string '{name}'")

        if var_type == "int" and rhs_type == "float":
            self._warn(f"Possible loss of precision assigning float to int '{name}'")

        if var_type == "char" and rhs_type == "float":
            self._warn(f"Assigning float to char '{name}'")


    def analyze(self, ast):
        for child in ast.children:
            if child.type == "FUNCTION":
                if child.value in self.functions:
                    self._error(f"Function '{child.value}' already declared")

                self.functions[child.value] = {
                    "params": child.children[0],
                    "return_type": "unknown",}

        self._visit(ast)

        return self.issues


    def _visit(self, node):
        if node is None:
            return
        method = getattr(self, f"_visit_{node.type}", self._visit_generic)
        method(node)

    def _visit_generic(self, node):
        for c in node.children:
            self._visit(c)
        self._visit(node.left)
        self._visit(node.right)


    def _visit_PROGRAM(self, node):
        for c in node.children:
            self._visit(c)

    def _visit_FUNCTION(self, node):
        prev = self._current_function
        self._current_function = node.value

        self._push_scope()

        for p in node.children[0]:
            self._declare(p, "int")
            self._mark_used(p)

        for stmt in node.children[1]:
            self._visit(stmt)

        self._pop_scope()
        self._current_function = prev

    def _visit_DECLLIST(self, node):
        for child in node.children:
            if child.type == "DECL":
                self._declare(child.value, node.value)

            elif child.type == "ASSIGN":
                self._declare(child.value, node.value)
                self._check_assign_types(child.value, node.value, child.left)
                self._visit(child.left)

            else:
                self._visit(child)

    def _visit_ASSIGN(self, node):
        info = self._lookup(node.value)

        if info is None:
            self._error(f"Assignment to undeclared variable '{node.value}'")
        else:
            self._mark_used(node.value)
            self._check_assign_types(node.value, info["type"], node.left)

        self._visit(node.left)

    def _visit_IDENTIFIER(self, node):
        if self._lookup(node.value) is None and node.value not in self.functions:
            self._error(f"Use of undeclared variable '{node.value}'")
        else:
            self._mark_used(node.value)

    def _visit_CALL(self, node):
        if node.value not in self.functions:
            self._error(f"Call to undeclared function '{node.value}'")
        else:
            expected = len(self.functions[node.value]["params"])
            got = len(node.children)

            if expected != got:
                self._warn(f"Function '{node.value}' expects {expected}, got {got}")

        for arg in node.children:
            self._visit(arg)

    def _visit_RETURN(self, node):
        if self._current_function is None:
            self._error("return outside function")
            return

        rtype = self._infer_type(node.left)
        self.functions[self._current_function]["return_type"] = rtype

        self._visit(node.left)

    def _validate_condition(self, node):
        t = self._infer_type(node)
        if t not in self.NUMERIC:
            self._warn(f"Condition uses non-numeric type '{t}'")

    def _visit_IF(self, node):
        self._validate_condition(node.left)

        self._push_scope()
        for s in node.children[0]:
            self._visit(s)
        self._pop_scope()

        if node.children[1]:
            self._push_scope()
            for s in node.children[1]:
                self._visit(s)
            self._pop_scope()

    def _visit_WHILE(self, node):
        self._validate_condition(node.left)

        self._push_scope()
        for s in node.children:
            self._visit(s)
        self._pop_scope()

    def _visit_FOR(self, node):
        self._push_scope()
        for part in node.children:
            if isinstance(part, list):
                for s in part:
                    self._visit(s)
            else:
                self._visit(part)
        self._pop_scope()

    def _visit_ARRAY_ASSIGN(self, node):
        if self._lookup(node.value) is None:
            self._error(f"Undeclared array '{node.value}'")

        self._visit(node.left)
        self._visit(node.right)

    def _visit_ARRAY_ACCESS(self, node):
        if self._lookup(node.value) is None:
            self._error(f"Undeclared array '{node.value}'")

        self._visit(node.left)

    def _visit_INC(self, node):
        if self._lookup(node.value) is None:
            self._error(f"Increment undeclared '{node.value}'")

    def _visit_DEC(self, node):
        if self._lookup(node.value) is None:
            self._error(f"Decrement undeclared '{node.value}'")

    def _visit_SCANF(self, node):
        for var in node.children:
            if self._lookup(var) is None:
                self._error(f"scanf undeclared '{var}'")
            else:
                self._mark_used(var)

    def _visit_PRINTF(self, node):
        for arg in node.children:
            self._visit(arg)

    def _visit_DIV(self, node):
        if node.right and node.right.type == "NUMBER" and node.right.value == "0":
            self._error("Division by zero")
        self._visit(node.left)
        self._visit(node.right)


class SemanticAnalysisError(Exception):
    def __init__(self, issues):
        self.issues = issues
        super().__init__(
            "\n".join(str(i) for i in issues if i.level == "ERROR")
        )
