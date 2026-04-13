# =============================================================
# semantic.py — Semantic Analyser for SimpleLang
#
# Responsibilities:
#   1. Build / populate the symbol table (scopes, types)
#   2. Type-check all expressions
#   3. Detect use-before-declaration
#   4. Detect duplicate declarations in the same scope
#   5. Report all errors before aborting (error recovery)
# =============================================================

from __future__ import annotations
from parser import (
    ProgramNode, DeclNode, AssignNode, IfNode, WhileNode,
    PrintNode, BlockNode, BinOpNode, UnaryOpNode, LiteralNode, IdentNode,
)
from symbol_table import SymbolTable


# Operator type rules:  (left_type, right_type) -> result_type
# 'num' is a wildcard for int|float; result is 'float' if either operand is float.
ARITH_OPS  = {"PLUS", "MINUS", "STAR", "SLASH", "PERCENT"}
REL_OPS    = {"LT", "GT", "LTE", "GTE"}
EQ_OPS     = {"EQ", "NEQ"}
LOGIC_OPS  = {"AND", "OR"}


class SemanticError(Exception):
    pass


class SemanticAnalyser:
    """
    Walks the AST, checks types and scopes, and annotates each IdentNode
    with the resolved Symbol object.  Returns the populated SymbolTable.
    """

    def __init__(self):
        self.sym_table = SymbolTable()
        self.errors: list[str] = []

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def analyse(self, tree: ProgramNode) -> SymbolTable:
        self._visit_program(tree)
        if self.errors:
            msg = "\n".join(f"  [SemanticError] {e}" for e in self.errors)
            raise SemanticError(f"Semantic analysis failed:\n{msg}")
        return self.sym_table

    # ------------------------------------------------------------------
    # Statement visitors
    # ------------------------------------------------------------------

    def _visit_program(self, node: ProgramNode):
        for stmt in node.stmts:
            self._visit_stmt(stmt)

    def _visit_stmt(self, node):
        match type(node).__name__:
            case "DeclNode":    self._visit_decl(node)
            case "AssignNode":  self._visit_assign(node)
            case "IfNode":      self._visit_if(node)
            case "WhileNode":   self._visit_while(node)
            case "PrintNode":   self._visit_print(node)
            case "BlockNode":   self._visit_block(node)
            case _:
                self._error(f"Unknown statement node: {type(node).__name__}")

    def _visit_decl(self, node: DeclNode):
        # Check for duplicate in current scope
        if self.sym_table.exists_in_current_scope(node.name):
            self._error(f"Variable '{node.name}' already declared in this scope.")
            return

        init_type = None
        if node.init is not None:
            init_type = self._visit_expr(node.init)
            if not self._types_compatible(node.var_type, init_type):
                self._error(
                    f"Type mismatch in declaration of '{node.name}': "
                    f"declared as '{node.var_type}' but initialised with '{init_type}'."
                )

        self.sym_table.insert(node.name, node.var_type)

    def _visit_assign(self, node: AssignNode):
        try:
            sym = self.sym_table.lookup(node.name)
        except NameError as e:
            self._error(str(e))
            return

        rhs_type = self._visit_expr(node.expr)
        if not self._types_compatible(sym.data_type, rhs_type):
            self._error(
                f"Type mismatch in assignment to '{node.name}': "
                f"variable is '{sym.data_type}' but expression is '{rhs_type}'."
            )

    def _visit_if(self, node: IfNode):
        cond_type = self._visit_expr(node.condition)
        if cond_type != "bool":
            self._error(f"'if' condition must be bool, got '{cond_type}'.")
        self.sym_table.enter_scope("if")
        self._visit_stmt(node.then_block)
        self.sym_table.exit_scope()
        if node.else_block:
            self.sym_table.enter_scope("else")
            self._visit_stmt(node.else_block)
            self.sym_table.exit_scope()

    def _visit_while(self, node: WhileNode):
        cond_type = self._visit_expr(node.condition)
        if cond_type != "bool":
            self._error(f"'while' condition must be bool, got '{cond_type}'.")
        self.sym_table.enter_scope("while")
        self._visit_stmt(node.body)
        self.sym_table.exit_scope()

    def _visit_print(self, node: PrintNode):
        self._visit_expr(node.expr)   # any type is printable

    def _visit_block(self, node: BlockNode):
        for stmt in node.stmts:
            self._visit_stmt(stmt)

    # ------------------------------------------------------------------
    # Expression visitors — return the inferred type string
    # ------------------------------------------------------------------

    def _visit_expr(self, node) -> str:
        match type(node).__name__:
            case "LiteralNode":  return self._visit_literal(node)
            case "IdentNode":    return self._visit_ident(node)
            case "BinOpNode":    return self._visit_binop(node)
            case "UnaryOpNode":  return self._visit_unary(node)
            case _:
                self._error(f"Unknown expression node: {type(node).__name__}")
                return "unknown"

    def _visit_literal(self, node: LiteralNode) -> str:
        return node.lit_type

    def _visit_ident(self, node: IdentNode) -> str:
        try:
            sym = self.sym_table.lookup(node.name)
            node.resolved_sym = sym          # annotate AST node
            return sym.data_type
        except NameError as e:
            self._error(str(e))
            return "unknown"

    def _visit_binop(self, node: BinOpNode) -> str:
        lt = self._visit_expr(node.left)
        rt = self._visit_expr(node.right)

        if node.op in ARITH_OPS:
            if lt not in ("int", "float") or rt not in ("int", "float"):
                self._error(
                    f"Arithmetic operator '{node.op}' requires numeric operands, "
                    f"got '{lt}' and '{rt}'."
                )
                return "unknown"
            return "float" if "float" in (lt, rt) else "int"

        if node.op in REL_OPS:
            if lt not in ("int", "float") or rt not in ("int", "float"):
                self._error(
                    f"Relational operator '{node.op}' requires numeric operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return "bool"

        if node.op in EQ_OPS:
            if lt != rt:
                self._error(
                    f"Equality operator '{node.op}' requires same-type operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return "bool"

        if node.op in LOGIC_OPS:
            if lt != "bool" or rt != "bool":
                self._error(
                    f"Logical operator '{node.op}' requires bool operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return "bool"

        self._error(f"Unknown binary operator: {node.op!r}")
        return "unknown"

    def _visit_unary(self, node: UnaryOpNode) -> str:
        ot = self._visit_expr(node.operand)
        if node.op == "NOT":
            if ot != "bool":
                self._error(f"'!' operator requires bool, got '{ot}'.")
            return "bool"
        if node.op == "MINUS":
            if ot not in ("int", "float"):
                self._error(f"Unary '-' requires numeric operand, got '{ot}'.")
            return ot
        self._error(f"Unknown unary operator: {node.op!r}")
        return "unknown"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _types_compatible(declared: str, actual: str) -> bool:
        if declared == actual:
            return True
        # Allow int literal assigned to float variable
        if declared == "float" and actual == "int":
            return True
        return False

    def _error(self, msg: str):
        self.errors.append(msg)


# ------------------------------------------------------------------
# Quick standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser

    src = """
    int x = 10;
    float y = 3.14;
    bool flag = true;
    if (x > 5) {
        print(x);
    }
    while (flag) {
        x = x + 1;
    }
    """
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    analyser = SemanticAnalyser()
    sym_table = analyser.analyse(ast)
    sym_table.display()
    print("Semantic analysis passed.")
