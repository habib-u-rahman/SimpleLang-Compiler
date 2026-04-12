# parser.py — AST node definitions for SimpleLang

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ProgramNode:
    stmts: List = field(default_factory=list)

@dataclass
class DeclNode:
    var_type: str
    name: str
    init: Optional[object] = None

@dataclass
class AssignNode:
    name: str
    expr: object = None

@dataclass
class IfNode:
    condition: object
    then_block: object
    else_block: Optional[object] = None

@dataclass
class WhileNode:
    condition: object
    body: object

@dataclass
class PrintNode:
    expr: object

@dataclass
class BlockNode:
    stmts: List = field(default_factory=list)

@dataclass
class BinOpNode:
    op: str
    left: object
    right: object

@dataclass
class UnaryOpNode:
    op: str
    operand: object

@dataclass
class LiteralNode:
    value: object
    lit_type: str

@dataclass
class IdentNode:
    name: str
