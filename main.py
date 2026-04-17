#!/usr/bin/env python3
# =============================================================
# main.py — SimpleLang Compiler Driver
#
# Usage:
#   python main.py <source_file>          # compile & run
#   python main.py <source_file> --dump   # compile, dump every
#                                         # phase, then run
#   python main.py --example              # run built-in demo
# =============================================================

import sys
import os

from lexer      import Lexer,            LexerError
from parser     import Parser,           ParseError
from semantic   import SemanticAnalyser, SemanticError
from intermediate import TACGenerator
from optimizer  import Optimizer
from codegen    import CodeGenerator,    VirtualMachine


# ------------------------------------------------------------------
# Built-in example program
# ------------------------------------------------------------------

EXAMPLE_SOURCE = """\
int a = 10;
int b = 3;
int sum = a + b;
int product = a * b;
bool big = a > 5;

print(sum);
print(product);

if (big) {
    print(a);
} else {
    print(b);
}

int counter = 0;
while (counter < 3) {
    print(counter);
    counter = counter + 1;
}
"""


# ------------------------------------------------------------------
# Compiler pipeline
# ------------------------------------------------------------------

def compile_and_run(source: str, dump: bool = False) -> bool:
    """
    Run the full compiler pipeline on *source* text.
    Returns True on success, False on any compile error.
    If *dump* is True, print the output of each phase.
    """

    # ── Phase 1: Lexical Analysis ──────────────────────────────
    print("\n[1/6] Lexical analysis …")
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"  Lexer error: {e}")
        return False

    if dump:
        print("  Tokens:")
        for tok in tokens:
            print(f"    {tok}")

    # ── Phase 2: Parsing ───────────────────────────────────────
    print("[2/6] Parsing …")
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
    except ParseError as e:
        print(f"  Parse error: {e}")
        return False

    if dump:
        import pprint
        print("  AST:")
        pprint.pprint(ast, indent=4)

    # ── Phase 3: Semantic Analysis ─────────────────────────────
    print("[3/6] Semantic analysis …")
    try:
        analyser  = SemanticAnalyser()
        sym_table = analyser.analyse(ast)
    except SemanticError as e:
        print(e)
        return False

    if dump:
        sym_table.display()

    # ── Phase 4: Intermediate Code Generation ─────────────────
    print("[4/6] Generating three-address code …")
    tac_gen = TACGenerator()
    tac     = tac_gen.generate(ast)

    if dump:
        tac_gen.print_code()

    # ── Phase 5: Optimisation ──────────────────────────────────
    print("[5/6] Optimising …")
    optimizer = Optimizer()
    opt_tac   = optimizer.optimize(tac)

    if dump:
        Optimizer.print_code(opt_tac, title="Optimised TAC")

    # ── Phase 6: Code Generation ───────────────────────────────
    print("[6/6] Generating target code …")
    cg  = CodeGenerator()
    asm = cg.generate(opt_tac)

    if dump:
        cg.print_code()

    # ── Execution ──────────────────────────────────────────────
    print("\n===== Program Output =====")
    VirtualMachine(asm).run()
    print("==========================\n")
    return True


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("SimpleLang Compiler\n")
        print("Usage:")
        print("  python main.py <source.sl>          # compile & run")
        print("  python main.py <source.sl> --dump   # dump each phase")
        print("  python main.py --example            # run built-in demo")
        return

    if args[0] == "--example":
        print("=== Running built-in example ===")
        compile_and_run(EXAMPLE_SOURCE, dump="--dump" in args)
        return

    source_file = args[0]
    dump = "--dump" in args

    if not os.path.isfile(source_file):
        print(f"Error: file not found: {source_file!r}")
        sys.exit(1)

    with open(source_file, "r", encoding="utf-8") as fh:
        source = fh.read()

    success = compile_and_run(source, dump=dump)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
