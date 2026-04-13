# semantic.py — Semantic analysis constants and error class

ARITH_OPS = {"PLUS", "MINUS", "STAR", "SLASH", "PERCENT"}
REL_OPS   = {"LT", "GT", "LTE", "GTE"}
EQ_OPS    = {"EQ", "NEQ"}
LOGIC_OPS = {"AND", "OR"}


class SemanticError(Exception):
    pass
