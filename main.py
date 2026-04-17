#!/usr/bin/env python3
# main.py — SimpleLang Compiler Driver (basic version)

import sys
from lexer      import Lexer,            LexerError
from parser     import Parser,           ParseError
from semantic   import SemanticAnalyser, SemanticError
from intermediate import TACGenerator
from optimizer  import Optimizer
from codegen    import CodeGenerator,    VirtualMachine


def compile_and_run(source: str) -> bool:
    print("\n[1/6] Lexical analysis ...")
    try:
        tokens = Lexer(source).tokenize()
    except LexerError as e:
        print(f"  Lexer error: {e}"); return False

    print("[2/6] Parsing ...")
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        print(f"  Parse error: {e}"); return False

    print("[3/6] Semantic analysis ...")
    try:
        SemanticAnalyser().analyse(ast)
    except SemanticError as e:
        print(e); return False

    print("[4/6] Generating three-address code ...")
    tac = TACGenerator().generate(ast)

    print("[5/6] Optimising ...")
    opt_tac = Optimizer().optimize(tac)

    print("[6/6] Generating target code ...")
    asm = CodeGenerator().generate(opt_tac)

    print("\n===== Program Output =====")
    VirtualMachine(asm).run()
    print("==========================\n")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source.sl>")
        return
    import os
    src_file = sys.argv[1]
    if not os.path.isfile(src_file):
        print(f"Error: file not found: {src_file!r}"); sys.exit(1)
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()
    compile_and_run(source)


if __name__ == "__main__":
    main()
