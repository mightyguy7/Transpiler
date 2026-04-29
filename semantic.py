from lexer import ASTNode


class SemanticError(Exception):
    pass


class SemanticWarning:
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"Warning: {self.message}"


class SemanticAnalyzer:

    def __init__(self):
        # Stack of scopes: each scope is a dict of name → type_info
        self.scope_stack = [{}]   # global scope
        self.functions   = {}     # name → {"params": [...], "return_type": str}
        self.warnings    = []

    # ── Scope management ──────────────────────────────────────────────────────

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        self.scope_stack.pop()

    def declare(self, name, type_info):
        """Declare in current (innermost) scope."""
        self.scope_stack[-1][name] = type_info

    def lookup(self, name):
        """Search from innermost to outermost scope."""
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def is_declared(self, name):
        return self.lookup(name) is not None

    # ── Visitor dispatch ──────────────────────────────────────────────────────

    def visit(self, node):
        if node is None:
            return
        method = getattr(self, f"visit_{node.type}", self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        if node.left:
            self.visit(node.left)
        if node.right:
            self.visit(node.right)
        for child in node.children:
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, ASTNode):
                        self.visit(c)
            elif isinstance(child, ASTNode):
                self.visit(child)

    # ── Program ───────────────────────────────────────────────────────────────

    def visit_PROGRAM(self, node):
        for child in node.children:
            self.visit(child)

    # ── Declarations ──────────────────────────────────────────────────────────

    def visit_DECLLIST(self, node):
        type_kw = node.value
        for var in node.children:
            name = var.value
            if name is not None:
                if name in self.scope_stack[-1]:
                    self.warnings.append(
                        SemanticWarning(f"Variable '{name}' re-declared in the same scope")
                    )
                self.declare(name, type_kw)
            self.visit(var)

    def visit_DECL(self, node):
        pass  # already handled by DECLLIST

    def visit_ARRAY_DECL(self, node):
        self.declare(node.value, "array")

    def visit_ARRAY_INIT(self, node):
        self.declare(node.value, "array")
        for c in node.children:
            self.visit(c)

    # ── Assignment ────────────────────────────────────────────────────────────

    def visit_ASSIGN(self, node):
        # Auto-declare if not yet seen (handles C99 for-loop inits etc.)
        if not self.is_declared(node.value):
            self.declare(node.value, "auto")
        self.visit(node.left)

    def visit_ARRAY_ASSIGN(self, node):
        if not self.is_declared(node.value):
            self.warnings.append(
                SemanticWarning(f"Array '{node.value}' assigned before declaration")
            )
            self.declare(node.value, "array")
        self.visit(node.left)
        self.visit(node.right)

    def visit_ARRAY_ACCESS(self, node):
        if not self.is_declared(node.value):
            self.warnings.append(
                SemanticWarning(f"Array '{node.value}' used before declaration")
            )
        self.visit(node.left)

    # ── Compound assignments ───────────────────────────────────────────────────

    def _visit_compound(self, node):
        lhs = node.left
        if lhs and lhs.type == "IDENTIFIER" and not self.is_declared(lhs.value):
            raise SemanticError(
                f"Variable '{lhs.value}' used in compound assignment before declaration"
            )
        self.generic_visit(node)

    def visit_PLUSEQ(self, node):   self._visit_compound(node)
    def visit_MINUSEQ(self, node):  self._visit_compound(node)
    def visit_MULEQ(self, node):    self._visit_compound(node)
    def visit_DIVEQ(self, node):    self._visit_compound(node)
    def visit_MODEQ(self, node):    self._visit_compound(node)

    # ── Identifiers ───────────────────────────────────────────────────────────

    def visit_IDENTIFIER(self, node):
        if not self.is_declared(node.value):
            self.warnings.append(
                SemanticWarning(f"Variable '{node.value}' used before declaration")
            )

    # ── Increment / Decrement ─────────────────────────────────────────────────

    def visit_INC(self, node):
        if not self.is_declared(node.value):
            raise SemanticError(f"Variable '{node.value}' incremented before declaration")

    def visit_DEC(self, node):
        if not self.is_declared(node.value):
            raise SemanticError(f"Variable '{node.value}' decremented before declaration")

    def visit_POST_INC(self, node):
        if node.left:
            self.visit(node.left)

    def visit_POST_DEC(self, node):
        if node.left:
            self.visit(node.left)

    # ── Control flow ──────────────────────────────────────────────────────────

    def visit_IF(self, node):
        self.visit(node.left)           # condition
        self.push_scope()
        for stmt in node.children[0]:   # if-body
            self.visit(stmt)
        self.pop_scope()
        self.push_scope()
        for stmt in node.children[1]:   # else-body
            self.visit(stmt)
        self.pop_scope()

    def visit_WHILE(self, node):
        self.visit(node.left)
        self.push_scope()
        for stmt in node.children:
            self.visit(stmt)
        self.pop_scope()

    def visit_DO_WHILE(self, node):
        self.push_scope()
        for stmt in node.children:
            self.visit(stmt)
        self.pop_scope()
        self.visit(node.left)

    def visit_FOR(self, node):
        self.push_scope()
        self.visit(node.children[0])   # init
        self.visit(node.children[1])   # condition
        self.visit(node.children[2])   # increment
        for stmt in node.children[3]:  # body
            self.visit(stmt)
        self.pop_scope()

    def visit_BREAK(self, node):    pass
    def visit_CONTINUE(self, node): pass

    # ── Functions ─────────────────────────────────────────────────────────────

    def visit_FUNCTION(self, node):
        name   = node.value
        params = node.children[0]   # list of strings
        body   = node.children[1]   # list of ASTNodes

        # Register function signature in global scope
        self.functions[name] = {"params": params, "return_type": "auto"}
        self.declare(name, "function")

        self.push_scope()
        for p in params:
            self.declare(p, "param")
        for stmt in body:
            self.visit(stmt)
        self.pop_scope()

    def visit_RETURN(self, node):
        if node.left:
            self.visit(node.left)

    # ── Calls ─────────────────────────────────────────────────────────────────

    def visit_CALL(self, node):
        # Check argument count if function is defined
        if node.value in self.functions:
            expected = len(self.functions[node.value]["params"])
            actual   = len(node.children)
            if actual != expected:
                self.warnings.append(
                    SemanticWarning(
                        f"Function '{node.value}' called with {actual} arg(s), "
                        f"expected {expected}"
                    )
                )
        for a in node.children:
            self.visit(a)

    # ── I/O ───────────────────────────────────────────────────────────────────

    def visit_PRINTF(self, node):
        import re
        fmt        = node.value
        specifiers = re.findall(r'%(?:lld|ld|lf|[dfiucs])', fmt)
        args       = node.children

        if len(specifiers) != len(args):
            self.warnings.append(
                SemanticWarning(
                    f"printf: {len(specifiers)} format specifier(s) but "
                    f"{len(args)} argument(s)"
                )
            )
        for a in args:
            self.visit(a)

    def visit_SCANF(self, node):
        import re
        fmt        = node.value
        specifiers = re.findall(r'%(?:lld|ld|lf|[dfiucs])', fmt)
        vars_      = node.children

        if len(specifiers) != len(vars_):
            self.warnings.append(
                SemanticWarning(
                    f"scanf: {len(specifiers)} format specifier(s) but "
                    f"{len(vars_)} variable(s)"
                )
            )

        # Determine type from specifier and declare variable
        spec_to_type = {
            "%d": "int",   "%i": "int",   "%u": "int",
            "%ld": "long", "%lld": "long long",
            "%f": "float", "%lf": "double",
            "%c": "char",  "%s": "char",
        }
        for i, var in enumerate(vars_):
            if isinstance(var, ASTNode) and var.value:
                spec  = specifiers[i] if i < len(specifiers) else "%d"
                dtype = spec_to_type.get(spec, "int")
                if not self.is_declared(var.value):
                    self.declare(var.value, dtype)

    # ── Misc ──────────────────────────────────────────────────────────────────

    def visit_COMMENT(self, node):
        pass

    def visit_BLOCK(self, node):
        self.push_scope()
        for stmt in node.children:
            self.visit(stmt)
        self.pop_scope()

    def visit_NUMBER(self, node):   pass
    def visit_STRING(self, node):   pass
    def visit_CHAR(self, node):     pass
    def visit_COMPARE(self, node):  self.generic_visit(node)
    def visit_ADD(self, node):      self.generic_visit(node)
    def visit_SUB(self, node):      self.generic_visit(node)
    def visit_MUL(self, node):      self.generic_visit(node)
    def visit_DIV(self, node):      self.generic_visit(node)
    def visit_MOD(self, node):      self.generic_visit(node)
    def visit_AND(self, node):      self.generic_visit(node)
    def visit_OR(self, node):       self.generic_visit(node)
    def visit_NOT(self, node):      self.generic_visit(node)