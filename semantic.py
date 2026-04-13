# semantic.py — Semantic analysis skeleton

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
        raise NotImplementedError("Visitors coming soon")

    def _error(self, msg: str):
        self.errors.append(msg)
