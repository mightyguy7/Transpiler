from lexer import ASTNode


class Optimizer:

    def optimize(self, node):
        if node is None:
            return None
        method = getattr(self, f"optimize_{node.type}", self.generic_optimize)
        return method(node)

    def generic_optimize(self, node):
        if node.left:
            node.left = self.optimize(node.left)
        if node.right:
            node.right = self.optimize(node.right)

        new_children = []
        for c in node.children:
            if isinstance(c, list):
                new_children.append(
                    [self.optimize(x) if isinstance(x, ASTNode) else x for x in c]
                )
            elif isinstance(c, ASTNode):
                new_children.append(self.optimize(c))
            else:
                new_children.append(c)

        node.children = new_children
        return node

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_number(self, node):
        return node is not None and node.type == "NUMBER"

    def _num_val(self, node):
        return float(node.value)

    def make_number(self, val):
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return ASTNode("NUMBER", str(val))

    # ── Constant folding + identity elimination ───────────────────────────────

    def optimize_ADD(self, node):
        node = self.generic_optimize(node)
        L, R = node.left, node.right
        # constant folding
        if self._is_number(L) and self._is_number(R):
            return self.make_number(self._num_val(L) + self._num_val(R))
        # identity: x + 0  or  0 + x  → x
        if self._is_number(R) and self._num_val(R) == 0:
            return L
        if self._is_number(L) and self._num_val(L) == 0:
            return R
        return node

    def optimize_SUB(self, node):
        node = self.generic_optimize(node)
        L, R = node.left, node.right
        if self._is_number(L) and self._is_number(R):
            return self.make_number(self._num_val(L) - self._num_val(R))
        # identity: x - 0 → x
        if self._is_number(R) and self._num_val(R) == 0:
            return L
        return node

    def optimize_MUL(self, node):
        node = self.generic_optimize(node)
        L, R = node.left, node.right
        if self._is_number(L) and self._is_number(R):
            return self.make_number(self._num_val(L) * self._num_val(R))
        # identity: x * 1  or  1 * x  → x
        if self._is_number(R) and self._num_val(R) == 1:
            return L
        if self._is_number(L) and self._num_val(L) == 1:
            return R
        # annihilator: x * 0  or  0 * x  → 0
        if self._is_number(R) and self._num_val(R) == 0:
            return self.make_number(0)
        if self._is_number(L) and self._num_val(L) == 0:
            return self.make_number(0)
        return node

    def optimize_DIV(self, node):
        node = self.generic_optimize(node)
        L, R = node.left, node.right
        if self._is_number(L) and self._is_number(R):
            divisor = self._num_val(R)
            if divisor == 0:
                return node  # don't fold / 0
            return self.make_number(self._num_val(L) / divisor)
        # identity: x / 1 → x
        if self._is_number(R) and self._num_val(R) == 1:
            return L
        return node

    def optimize_MOD(self, node):
        node = self.generic_optimize(node)
        L, R = node.left, node.right
        if self._is_number(L) and self._is_number(R):
            divisor = self._num_val(R)
            if divisor == 0:
                return node
            result = self._num_val(L) % divisor
            return self.make_number(result)
        # identity: x % 1 → 0
        if self._is_number(R) and self._num_val(R) == 1:
            return self.make_number(0)
        return node

    # ── Compound assignment identity elimination ──────────────────────────────

    def optimize_PLUSEQ(self, node):
        node = self.generic_optimize(node)
        # x += 0 → (no-op, but we can't remove it easily; return as-is)
        if self._is_number(node.right) and self._num_val(node.right) == 0:
            return None  # signal: remove this statement
        return node

    def optimize_MINUSEQ(self, node):
        node = self.generic_optimize(node)
        if self._is_number(node.right) and self._num_val(node.right) == 0:
            return None
        return node

    def optimize_MULEQ(self, node):
        node = self.generic_optimize(node)
        if self._is_number(node.right) and self._num_val(node.right) == 1:
            return None
        return node

    def optimize_DIVEQ(self, node):
        node = self.generic_optimize(node)
        if self._is_number(node.right) and self._num_val(node.right) == 1:
            return None
        return node

    def optimize_MODEQ(self, node):
        node = self.generic_optimize(node)
        return node

    # ── Assignment: fold right-hand side, then check for self-assignment ──────

    def optimize_ASSIGN(self, node):
        node = self.generic_optimize(node)
        L = node.left  # the rhs expression
        # If rhs reduces to the same variable name, it's a no-op assignment
        # e.g. a = a  (after folding a + 0 → a the rhs is IDENTIFIER 'a')
        if (L is not None and L.type == "IDENTIFIER" and L.value == node.value):
            return None  # remove no-op
        return node

    # ── Dead-branch elimination ───────────────────────────────────────────────

    def optimize_IF(self, node):
        node.left = self.optimize(node.left)

        if node.left and node.left.type == "NUMBER":
            taken = node.children[0] if self._num_val(node.left) != 0 else node.children[1]
            optimised = [self.optimize(s) for s in taken if isinstance(s, ASTNode)]
            optimised = [s for s in optimised if s is not None]

            if not optimised:
                return None

            if len(optimised) == 1:
                return optimised[0]

            block = ASTNode("BLOCK", children=optimised)
            return block

        return self.generic_optimize(node)

    # ── List-aware block optimization (removes None stmts) ────────────────────

    def _optimize_stmts(self, stmts):
        result = []
        for s in stmts:
            if not isinstance(s, ASTNode):
                result.append(s)
                continue
            opt = self.optimize(s)
            if opt is not None:
                result.append(opt)
        return result

    def optimize_FUNCTION(self, node):
        params = node.children[0]
        body   = node.children[1]
        node.children = [params, self._optimize_stmts(body)]
        return node

    def optimize_WHILE(self, node):
        node.left    = self.optimize(node.left)
        node.children = self._optimize_stmts(node.children)
        return node

    def optimize_DO_WHILE(self, node):
        node.children = self._optimize_stmts(node.children)
        node.left     = self.optimize(node.left)
        return node

    def optimize_FOR(self, node):
        init      = self.optimize(node.children[0])
        condition = self.optimize(node.children[1])
        increment = self.optimize(node.children[2])
        body      = self._optimize_stmts(node.children[3])
        node.children = [init, condition, increment, body]
        return node

    def optimize_PROGRAM(self, node):
        node.children = self._optimize_stmts(node.children)
        return node

    def optimize_DECLLIST(self, node):
        new_vars = []
        for child in node.children:
            opt = self.optimize(child)
            if opt is not None:
                new_vars.append(opt)
        node.children = new_vars
        return node

    def optimize_BLOCK(self, node):
        node.children = self._optimize_stmts(node.children)
        return node