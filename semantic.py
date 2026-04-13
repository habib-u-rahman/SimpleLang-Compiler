# semantic.py — Semantic analyser with statement visitors

from parser import (ProgramNode, DeclNode, AssignNode, IfNode, WhileNode,
                    PrintNode, BlockNode, BinOpNode, UnaryOpNode, LiteralNode, IdentNode)
from symbol_table import SymbolTable

ARITH_OPS = {"PLUS", "MINUS", "STAR", "SLASH", "PERCENT"}
REL_OPS   = {"LT", "GT", "LTE", "GTE"}
EQ_OPS    = {"EQ", "NEQ"}
LOGIC_OPS = {"AND", "OR"}


class SemanticError(Exception):
    pass


class SemanticAnalyser:
    def __init__(self):
        self.sym_table = SymbolTable()
        self.errors: list[str] = []

    def analyse(self, tree):
        self._visit_program(tree)
        if self.errors:
            msg = "\n".join(f"  [SemanticError] {e}" for e in self.errors)
            raise SemanticError(f"Semantic analysis failed:\n{msg}")
        return self.sym_table

    def _visit_program(self, node):
        for stmt in node.stmts:
            self._visit_stmt(stmt)

    def _visit_stmt(self, node):
        match type(node).__name__:
            case "DeclNode":   self._visit_decl(node)
            case "AssignNode": self._visit_assign(node)
            case "IfNode":     self._visit_if(node)
            case "WhileNode":  self._visit_while(node)
            case "PrintNode":  self._visit_print(node)
            case "BlockNode":  self._visit_block(node)
            case _: self._error(f"Unknown statement: {type(node).__name__}")

    def _visit_decl(self, node):
        if self.sym_table.exists_in_current_scope(node.name):
            self._error(f"Variable '{node.name}' already declared in this scope.")
            return
        if node.init is not None:
            self._visit_expr(node.init)
        self.sym_table.insert(node.name, node.var_type)

    def _visit_assign(self, node):
        try:
            self.sym_table.lookup(node.name)
        except NameError as e:
            self._error(str(e)); return
        self._visit_expr(node.expr)

    def _visit_if(self, node):
        self._visit_expr(node.condition)
        self.sym_table.enter_scope("if")
        self._visit_stmt(node.then_block)
        self.sym_table.exit_scope()
        if node.else_block:
            self.sym_table.enter_scope("else")
            self._visit_stmt(node.else_block)
            self.sym_table.exit_scope()

    def _visit_while(self, node):
        self._visit_expr(node.condition)
        self.sym_table.enter_scope("while")
        self._visit_stmt(node.body)
        self.sym_table.exit_scope()

    def _visit_print(self, node):
        self._visit_expr(node.expr)

    def _visit_block(self, node):
        for stmt in node.stmts:
            self._visit_stmt(stmt)

    def _visit_expr(self, node) -> str:
        return "unknown"

    def _error(self, msg: str):
        self.errors.append(msg)
