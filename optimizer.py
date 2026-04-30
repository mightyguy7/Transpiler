from lexer import ASTNode
class Optimizer:

    def optimize(self, node):
        if node is None:
            return None

        
        if isinstance(node, list):
            return [self.optimize(n) for n in node]

        
        if not hasattr(node, "type"):
            return node

        method = getattr(self, f"_opt_{node.type}", self._generic)
        return method(node)

    

    def _generic(self, node):
        if not hasattr(node, "type"):
            return node

        if node.left:
            node.left = self.optimize(node.left)
        if node.right:
            node.right = self.optimize(node.right)

        new_children = []
        for c in node.children:
            if isinstance(c, list):
                new_children.append([self.optimize(x) for x in c])
            elif hasattr(c, "type"):
                new_children.append(self.optimize(c))
            else:
                new_children.append(c)

        node.children = new_children
        return node

    

    def _is_number(self, node):
        return node and node.type == "NUMBER"

    def _num(self, node):
        return float(node.value)

    def _make_number(self, val):
        if int(val) == val:
            return ASTNode("NUMBER", str(int(val)))
        return ASTNode("NUMBER", str(val))

    def _fold_binary(self, node, op):
        if self._is_number(node.left) and self._is_number(node.right):
            l = self._num(node.left)
            r = self._num(node.right)

            if op == "+":
                return self._make_number(l + r)
            if op == "-":
                return self._make_number(l - r)
            if op == "*":
                return self._make_number(l * r)
            if op == "/":
                if r != 0:
                    return self._make_number(l / r)
            if op == "%":
                if r != 0:
                    return self._make_number(l % r)

        return node

    

    def _opt_ADD(self, node):
        node = self._generic(node)

        
        if self._is_number(node.right) and node.right.value == "0":
            return node.left
        if self._is_number(node.left) and node.left.value == "0":
            return node.right

        return self._fold_binary(node, "+")

    

    def _opt_SUB(self, node):
        node = self._generic(node)

        
        if self._is_number(node.right) and node.right.value == "0":
            return node.left

        return self._fold_binary(node, "-")

    

    def _opt_MUL(self, node):
        node = self._generic(node)

        
        if self._is_number(node.right) and node.right.value == "1":
            return node.left
        if self._is_number(node.left) and node.left.value == "1":
            return node.right

        
        if self._is_number(node.right) and node.right.value == "0":
            return ASTNode("NUMBER", "0")
        if self._is_number(node.left) and node.left.value == "0":
            return ASTNode("NUMBER", "0")

        return self._fold_binary(node, "*")

    

    def _opt_DIV(self, node):
        node = self._generic(node)

        
        if self._is_number(node.right) and node.right.value == "1":
            return node.left

        return self._fold_binary(node, "/")

    

    def _opt_MOD(self, node):
        node = self._generic(node)
        return self._fold_binary(node, "%")

    

    def _opt_PROGRAM(self, node):
        
        node = self._generic(node)

        
        env = {}
        new_children = []

        for stmt in node.children:
            if stmt.type == "DECLLIST":
                stmt = self._decllist_propagate(stmt, env)
            else:
                stmt = self._propagate(stmt, env)

            if stmt:
                new_children.append(stmt)

        node.children = new_children

        
        node = self._generic(node)

        return node
    
    def _decllist_propagate(self, node, env):
        new_children = []

        for child in node.children:
            child = self._propagate(child, env)
            if child:
                new_children.append(child)

        node.children = new_children
        return node
    
    def _propagate(self, node, env):
        if node is None:
            return None

        if isinstance(node, list):
            return [self._propagate(n, env) for n in node]

        # 🔴 FIX
        if not hasattr(node, "type"):
            return node

        if node.type == "ASSIGN":
            node.left = self._propagate(node.left, env)

            if hasattr(node.left, "type") and node.left.type == "NUMBER":
                env[node.value] = node.left.value
            else:
                env.pop(node.value, None)

            return node

        if node.type == "IDENTIFIER":
            if node.value in env:
                return ASTNode("NUMBER", env[node.value])
            return node

        if node.left:
            node.left = self._propagate(node.left, env)
        if node.right:
            node.right = self._propagate(node.right, env)

        new_children = []
        for c in node.children:
            if isinstance(c, list):
                new_children.append([self._propagate(x, env) for x in c])
            elif hasattr(c, "type"):
                new_children.append(self._propagate(c, env))
            else:
                new_children.append(c)

        node.children = new_children
        return node
