# intermediate.py — Three-Address Code (TAC) instruction class

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TAC:
    op: str
    result: str | None = None
    arg1: object = None
    arg2: object = None

    def __str__(self):
        match self.op:
            case "assign": return f"    {self.result} = {self.arg1}"
            case "binop":  return f"    {self.result} = {self.arg1} {self.arg2[0]} {self.arg2[1]}"
            case "unary":  return f"    {self.result} = {self.arg1}{self.arg2}"
            case "label":  return f"{self.result}:"
            case "jump":   return f"    goto {self.arg1}"
            case "cjump":
                tl, fl = self.arg2
                return f"    if {self.arg1} goto {tl} else goto {fl}"
            case "print":  return f"    print {self.arg1}"
            case _:        return f"    {self.op} {self.result} {self.arg1} {self.arg2}"
