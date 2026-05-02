#!/usr/bin/env python3
# gui.py — SimpleLang Compiler IDE  ·  Slate/Indigo Design v2
# Run:  python gui.py

import tkinter as tk
from tkinter import ttk, filedialog
import io, sys, re

from lexer        import Lexer,            LexerError
from parser       import Parser,           ParseError
from semantic     import SemanticAnalyser, SemanticError
from intermediate import TACGenerator
from optimizer    import Optimizer
from codegen      import CodeGenerator,    VirtualMachine

# ── Colour Palette  (Slate · Indigo) ─────────────────────────────────────────
BG       = "#0f172a"   # slate-900   main background
SURF     = "#1e293b"   # slate-800   surfaces / panels
SURF2    = "#334155"   # slate-700   hover / borders
BORDER   = "#475569"   # slate-600
ACCENT   = "#6366f1"   # indigo-500  primary
ACCENT_L = "#818cf8"   # indigo-400  lighter accent
GREEN    = "#22c55e"   # green-500
GREEN_D  = "#16a34a"   # green-700   run button hover
RED      = "#ef4444"   # red-500
AMBER    = "#f59e0b"   # amber-500
CYAN     = "#06b6d4"   # cyan-500
PINK     = "#ec4899"   # pink-500
PURPLE   = "#a855f7"   # purple-500
TEXT     = "#f1f5f9"   # slate-100   main text
DIM      = "#94a3b8"   # slate-400   secondary text
DIM2     = "#64748b"   # slate-500   placeholder / dim
EDITOR   = "#070d1a"   # code editor bg (darkest)

# syntax colours inside editor
SYN = dict(kw=ACCENT_L, num=AMBER, str=GREEN, boo=CYAN,
           op=BLUE_SYN := "#7dd3fc", cmt=DIM2)

# token-type → treeview row tag
def _tt_tag(tt: str) -> str:
    KW  = {"INT","FLOAT_KW","BOOL_KW","STRING_KW","IF","ELSE","WHILE","PRINT"}
    LIT = {"INTEGER","FLOAT","STRING","TRUE","FALSE"}
    OPS = {"PLUS","MINUS","STAR","SLASH","PERCENT","EQ","NEQ",
           "LT","GT","LTE","GTE","AND","OR","NOT","ASSIGN"}
    if tt in KW:      return "kw"
    if tt in LIT:     return "lit"
    if tt == "IDENT": return "idn"
    if tt in OPS:     return "ops"
    if tt == "EOF":   return "eof"
    return "dlm"


# ── Hover-aware button ────────────────────────────────────────────────────────
class HoverBtn(tk.Button):
    def __init__(self, parent, hover_bg, hover_fg="#ffffff", **kw):
        self._bg0 = kw.get("bg", SURF)
        self._fg0 = kw.get("fg", TEXT)
        self._bg1 = hover_bg
        self._fg1 = hover_fg
        super().__init__(parent, relief="flat", bd=0, cursor="hand2", **kw)
        self.bind("<Enter>", lambda _: self.config(bg=self._bg1, fg=self._fg1))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg0, fg=self._fg0))


# ── Treeview helper ───────────────────────────────────────────────────────────
def make_tree(parent, cols: list[tuple]) -> ttk.Treeview:
    """cols = [(id, heading, width), ...]"""
    f = tk.Frame(parent, bg=BG)
    f.pack(fill="both", expand=True)
    ids  = [c[0] for c in cols]
    tree = ttk.Treeview(f, columns=ids, show="headings",
                        style="SL.Treeview")
    for cid, head, w in cols:
        tree.heading(cid, text=head)
        tree.column(cid, width=w, minwidth=30, anchor="w")
    sby = ttk.Scrollbar(f, orient="vertical",   command=tree.yview)
    sbx = ttk.Scrollbar(f, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
    sby.pack(side="right",  fill="y")
    sbx.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    return tree


# ── Coloured Text helper ──────────────────────────────────────────────────────
def make_txt(parent) -> tk.Text:
    f = tk.Frame(parent, bg=BG)
    f.pack(fill="both", expand=True)
    t = tk.Text(f, bg=BG, fg=TEXT, font=("Consolas", 11),
                relief="flat", padx=16, pady=12,
                state="disabled", selectbackground=SURF2,
                wrap="none", insertbackground=ACCENT)
    # colour tags
    cfg = dict(
        acc=(ACCENT,),   bl=(ACCENT_L,), gr=(GREEN,),  rd=(RED,),
        am=(AMBER,),     cy=(CYAN,),     pk=(PINK,),   pu=(PURPLE,),
        tx=(TEXT,),      dm=(DIM,),      dm2=(DIM2,),
        bold_acc=(ACCENT, None, "bold"), bold_dm=(DIM, None, "italic"),
        lbl=(ACCENT, None, "bold"),      jmp=(AMBER,),
        prt=(GREEN,),    asn=(CYAN,),    bin=(ACCENT_L,),
        hlt=(RED, None, "bold"),
    )
    for name, vals in cfg.items():
        fg = vals[0]
        bg = vals[1] if len(vals) > 1 else None
        fn_style = vals[2] if len(vals) > 2 else None
        opts: dict = dict(foreground=fg)
        if bg:        opts["background"] = bg
        if fn_style:  opts["font"] = ("Consolas", 11, fn_style)
        t.tag_config(name, **opts)
    sby = ttk.Scrollbar(f, orient="vertical",   command=t.yview)
    sbx = ttk.Scrollbar(f, orient="horizontal", command=t.xview)
    t.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
    sby.pack(side="right",  fill="y")
    sbx.pack(side="bottom", fill="x")
    t.pack(fill="both", expand=True)
    return t


def txt_put(t: tk.Text, segs: list[tuple[str, str]]):
    t.configure(state="normal")
    t.delete("1.0", "end")
    for content, tag in segs:
        t.insert("end", content, tag)
    t.configure(state="disabled")


def tv_clear(tv: ttk.Treeview):
    for r in tv.get_children(): tv.delete(r)


# ── AST  pretty-printer ───────────────────────────────────────────────────────
def ast_segs(node, prefix="", last=True) -> list[tuple[str, str]]:
    conn   = "└─ " if last else "├─ "
    branch = "   " if last else "│  "
    name   = type(node).__name__
    out    = [(prefix + conn, "dm2"), (name, "bold_acc")]

    if   name == "LiteralNode":  out += [(f"  {node.value!r}", "am"),
                                          (f"  :{node.lit_type}", "dm")]
    elif name == "IdentNode":    out += [(f"  '{node.name}'", "pk")]
    elif name == "BinOpNode":    out += [(f"  [{node.op}]", "bl")]
    elif name == "UnaryOpNode":  out += [(f"  [{node.op}]", "bl")]
    elif name == "DeclNode":     out += [(f"  {node.var_type} ", "cy"),
                                          (f"'{node.name}'", "pk")]
    elif name == "AssignNode":   out += [(f"  '{node.name}'", "pk")]
    out.append(("\n", "tx"))

    kids = []
    if   name == "ProgramNode":  kids = node.stmts
    elif name == "DeclNode":
        if node.init: kids = [node.init]
    elif name == "AssignNode":
        if node.expr: kids = [node.expr]
    elif name == "IfNode":
        kids = [node.condition, node.then_block]
        if node.else_block: kids.append(node.else_block)
    elif name == "WhileNode":    kids = [node.condition, node.body]
    elif name == "PrintNode":    kids = [node.expr]
    elif name == "BlockNode":    kids = node.stmts
    elif name == "BinOpNode":    kids = [node.left, node.right]
    elif name == "UnaryOpNode":  kids = [node.operand]

    for i, kid in enumerate(kids):
        out += ast_segs(kid, prefix + branch, i == len(kids) - 1)
    return out


# ── TAC  renderer ─────────────────────────────────────────────────────────────
def render_tac(t: tk.Text, instrs):
    t.configure(state="normal")
    t.delete("1.0", "end")
    for ins in instrs:
        if ins.op == "label":
            t.insert("end", f"\n{ins.result}:\n", "lbl")
        elif ins.op == "assign":
            vtag = "am" if isinstance(ins.arg1, (int, float, bool)) else "pk"
            t.insert("end", f"    {ins.result}", "asn")
            t.insert("end", "  ←  ", "dm2")
            t.insert("end", f"{ins.arg1}\n", vtag)
        elif ins.op == "binop":
            sym, rhs = ins.arg2
            rtag = "am" if isinstance(rhs, (int, float, bool)) else "pk"
            t.insert("end", f"    {ins.result}", "asn")
            t.insert("end", "  ←  ", "dm2")
            t.insert("end", f"{ins.arg1}", "pk")
            t.insert("end", f"  {sym}  ", "bin")
            t.insert("end", f"{rhs}\n", rtag)
        elif ins.op == "unary":
            t.insert("end", f"    {ins.result}", "asn")
            t.insert("end", "  ←  ", "dm2")
            t.insert("end", f"{ins.arg1}", "bin")
            t.insert("end", f"{ins.arg2}\n", "pk")
        elif ins.op == "cjump":
            tl, fl = ins.arg2
            t.insert("end", "    if  ", "dm")
            t.insert("end", f"{ins.arg1}", "cy")
            t.insert("end", "  →  ", "dm2")
            t.insert("end", f"{tl}", "gr")
            t.insert("end", "  else  ", "dm2")
            t.insert("end", f"{fl}\n", "am")
        elif ins.op == "jump":
            t.insert("end", "    goto  ", "jmp")
            t.insert("end", f"{ins.arg1}\n", "am")
        elif ins.op == "print":
            t.insert("end", "    print  ", "prt")
            t.insert("end", f"{ins.arg1}\n", "cy")
    t.configure(state="disabled")


# ── Assembly  renderer ────────────────────────────────────────────────────────
def render_asm(t: tk.Text, instrs):
    from codegen import LabelInstr
    OPC = {
        "PUSH":"bl","LOAD":"bl","STORE":"asn",
        "ADD":"tx","SUB":"tx","MUL":"tx","DIV":"tx","MOD":"tx",
        "EQ":"tx","NEQ":"tx","LT":"tx","GT":"tx","LTE":"tx","GTE":"tx",
        "AND":"tx","OR":"tx","NOT":"tx","NEG":"tx",
        "JMP":"jmp","JIF":"jmp","PRINT":"prt","HALT":"hlt",
    }
    t.configure(state="normal")
    t.delete("1.0", "end")
    for ins in instrs:
        if isinstance(ins, LabelInstr):
            t.insert("end", f"\n{ins.name}:\n", "lbl")
        else:
            tag = OPC.get(ins.op, "tx")
            t.insert("end", f"    {ins.op:<8}", tag)
            if ins.arg is not None:
                atag = "am" if isinstance(ins.arg, (int, float, bool)) else "pk"
                t.insert("end", f"  {ins.arg}", atag)
            t.insert("end", "\n")
    t.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
# Main  IDE
# ─────────────────────────────────────────────────────────────────────────────
class IDE:

    EXAMPLE = """\
int a = 10;
int b = 3;
int sum     = a + b;
int product = a * b;
bool big    = a > 5;

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

    PHASES = [
        ("LEX",   ACCENT_L),
        ("PARSE", CYAN),
        ("SEM",   GREEN),
        ("TAC",   AMBER),
        ("OPT",   PURPLE),
        ("ASM",   PINK),
    ]

    # ── setup ─────────────────────────────────────────────────────────────────
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SimpleLang Compiler IDE")
        self.root.geometry("1380x820")
        self.root.configure(bg=BG)
        self.root.minsize(1020, 660)
        self._set_icon()
        self._ttk_styles()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self.editor.insert("1.0", self.EXAMPLE)
        self._refresh()

    # ── window icon ───────────────────────────────────────────────────────────
    def _set_icon(self):
        try:
            ico = tk.PhotoImage(width=32, height=32)
            ico.put(ACCENT,   to=(0,  0,  32, 32))   # indigo base
            ico.put(ACCENT_L, to=(4,  4,  28, 14))   # top bar (S-like)
            ico.put(ACCENT_L, to=(4,  13, 16, 19))   # mid bar
            ico.put(ACCENT_L, to=(4,  18, 28, 28))   # bottom bar (L-like)
            ico.put(BG,       to=(16, 18, 28, 28))   # cut-out makes 'L'
            self.root.iconphoto(True, ico)
            self._icon_img = ico          # prevent GC
        except Exception:
            pass

    # ── TTK styles ─────────────────────────────────────────────────────────────
    def _ttk_styles(self):
        s = ttk.Style()
        s.theme_use("default")

        s.configure("TNotebook",
                    background=SURF, borderwidth=0,
                    tabmargins=[0, 4, 0, 0])
        s.configure("TNotebook.Tab",
                    background=SURF2, foreground=DIM,
                    font=("Consolas", 9, "bold"),
                    padding=[18, 8], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT),   ("active", BORDER)],
              foreground=[("selected", "#ffffff"), ("active", TEXT)])

        s.configure("SL.Treeview",
                    background=SURF, foreground=TEXT,
                    fieldbackground=SURF, rowheight=32,
                    font=("Consolas", 10), borderwidth=0, relief="flat")
        s.configure("SL.Treeview.Heading",
                    background=SURF2, foreground=ACCENT_L,
                    font=("Consolas", 10, "bold"),
                    relief="flat", padding=[10, 8])
        s.map("SL.Treeview",
              background=[("selected", BORDER)],
              foreground=[("selected", ACCENT_L)])
        s.map("SL.Treeview.Heading",
              background=[("active", BORDER)])

        s.configure("TScrollbar",
                    background=SURF2, troughcolor=SURF,
                    bordercolor=SURF, arrowcolor=DIM2,
                    relief="flat", width=10)
        s.map("TScrollbar",
              background=[("active", BORDER), ("pressed", ACCENT)])

    # ── Toolbar ────────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=SURF, height=60)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # brand
        tk.Label(bar, text=" ⟨/⟩ ", font=("Consolas", 16, "bold"),
                 bg=SURF, fg=ACCENT).pack(side="left", padx=(14, 0))
        tk.Label(bar, text="SimpleLang IDE",
                 font=("Consolas", 12), bg=SURF, fg=TEXT).pack(side="left")

        # divider
        tk.Frame(bar, bg=BORDER, width=2).pack(
            side="left", fill="y", padx=14, pady=14)

        # buttons
        def btn(lbl, cmd, bg, fg, hbg):
            HoverBtn(bar, text=lbl, command=cmd,
                     bg=bg, fg=fg, hover_bg=hbg,
                     font=("Consolas", 10, "bold"),
                     padx=18, pady=10).pack(side="left", padx=5, pady=10)

        btn("  ▶  RUN  ",     self._run,          GREEN,   "#0f172a", GREEN_D)
        btn("  ↺  RESET  ",   self._clear,        SURF2,   TEXT,      BORDER)
        btn("  ⊞  OPEN  ",    self._open_file,    SURF2,   TEXT,      BORDER)
        btn("  ⊟  SAVE  ",    self._save_file,    SURF2,   TEXT,      BORDER)
        btn("  ★  EXAMPLE  ", self._load_example, ACCENT,  "#ffffff",ACCENT_L)

        # divider
        tk.Frame(bar, bg=BORDER, width=2).pack(
            side="left", fill="y", padx=14, pady=14)

        # phase indicators
        self._phase_dots  = []
        self._phase_names = []
        for label, colour in self.PHASES:
            pf = tk.Frame(bar, bg=SURF)
            pf.pack(side="left", padx=8, pady=8)
            dot  = tk.Label(pf, text="⬤",  font=("Consolas", 13),
                            bg=SURF, fg=DIM2)
            name = tk.Label(pf, text=label, font=("Consolas", 7, "bold"),
                            bg=SURF, fg=DIM2)
            dot.pack()
            name.pack()
            self._phase_dots.append((dot, name, colour))

    def _phase(self, idx: int, state: str):
        """state: 'idle' | 'run' | 'ok' | 'err'"""
        dot, name, col = self._phase_dots[idx]
        c = {"idle": DIM2, "run": AMBER, "ok": col, "err": RED}[state]
        dot.configure(fg=c)
        name.configure(fg=c)
        self.root.update_idletasks()

    def _phases_reset(self):
        for i in range(len(self.PHASES)):
            self._phase(i, "idle")

    # ── Body ──────────────────────────────────────────────────────────────────
    def _build_body(self):
        paned = tk.PanedWindow(self.root, orient="horizontal",
                               bg=BORDER, sashwidth=5,
                               sashrelief="flat", sashpad=0, handlesize=0)
        paned.pack(fill="both", expand=True)

        # ── LEFT: editor ─────────────────────────────────────────────────────
        left = tk.Frame(paned, bg=SURF)
        paned.add(left, width=500, minsize=260)

        header_l = tk.Frame(left, bg=SURF2, height=30)
        header_l.pack(fill="x")
        header_l.pack_propagate(False)
        tk.Label(header_l, text="  SOURCE CODE  —  .sl",
                 font=("Consolas", 8, "bold"),
                 bg=SURF2, fg=DIM, anchor="w").pack(
                 side="left", fill="both", padx=8)

        outer = tk.Frame(left, bg=EDITOR)
        outer.pack(fill="both", expand=True)

        self.gutter = tk.Text(outer, width=4,
                              bg=SURF, fg=DIM2,
                              font=("Consolas", 12),
                              state="disabled", relief="flat",
                              padx=8, pady=8, cursor="arrow",
                              selectbackground=SURF)
        self.gutter.pack(side="left", fill="y")

        self.editor = tk.Text(outer, bg=EDITOR, fg=TEXT,
                              font=("Consolas", 12),
                              insertbackground=ACCENT,
                              relief="flat", padx=12, pady=8,
                              selectbackground=SURF2,
                              undo=True, wrap="none", tabs="4c")

        sby = ttk.Scrollbar(outer, orient="vertical",   command=self._ysync)
        sbx = ttk.Scrollbar(left,  orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=sby.set,
                              xscrollcommand=sbx.set)
        sby.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)
        sbx.pack(fill="x")

        # syntax tags
        self.editor.tag_config("kw",  foreground=ACCENT_L)
        self.editor.tag_config("num", foreground=AMBER)
        self.editor.tag_config("str", foreground=GREEN)
        self.editor.tag_config("boo", foreground=CYAN)
        self.editor.tag_config("op",  foreground="#7dd3fc")
        self.editor.tag_config("cmt", foreground=DIM2,
                               font=("Consolas", 12, "italic"))

        self.editor.bind("<KeyRelease>",    self._on_key)
        self.editor.bind("<ButtonRelease>", self._update_cursor)
        self.editor.bind("<MouseWheel>",    self._wheel)
        self.gutter.bind("<MouseWheel>",    self._wheel)

        # ── RIGHT: notebook ───────────────────────────────────────────────────
        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=260)

        header_r = tk.Frame(right, bg=SURF2, height=30)
        header_r.pack(fill="x")
        header_r.pack_propagate(False)
        tk.Label(header_r, text="  COMPILER OUTPUT",
                 font=("Consolas", 8, "bold"),
                 bg=SURF2, fg=DIM, anchor="w").pack(
                 side="left", fill="both", padx=8)

        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)

        # Output
        fo = tk.Frame(self.nb, bg=BG); self.nb.add(fo, text="  ▶  Output  ")
        self.t_out = make_txt(fo)

        # Tokens
        ft = tk.Frame(self.nb, bg=BG); self.nb.add(ft, text="  ⬡  Tokens  ")
        self.tv_tok = make_tree(ft, [
            ("#",     "#",      46),
            ("type",  "Type",  170),
            ("value", "Value", 210),
            ("line",  "Line",   70),
        ])
        for tag, col in [("kw", ACCENT_L), ("lit", AMBER), ("idn", PINK),
                         ("ops", "#7dd3fc"), ("dlm", TEXT), ("eof", DIM2)]:
            self.tv_tok.tag_configure(tag, foreground=col)

        # AST
        fa = tk.Frame(self.nb, bg=BG); self.nb.add(fa, text="  🌳  AST  ")
        self.t_ast = make_txt(fa)

        # Symbols
        fs = tk.Frame(self.nb, bg=BG); self.nb.add(fs, text="  ▦  Symbols  ")
        self.tv_sym = make_tree(fs, [
            ("name",  "Name",  160),
            ("type",  "Type",  110),
            ("scope", "Scope", 130),
            ("val",   "Value", 160),
        ])
        for tag, col in [("ti", AMBER), ("tf", AMBER),
                         ("tb", CYAN),  ("ts", GREEN)]:
            self.tv_sym.tag_configure(tag, foreground=col)

        # TAC
        fc = tk.Frame(self.nb, bg=BG); self.nb.add(fc, text="  ⚙  TAC  ")
        self.t_tac = make_txt(fc)

        # Opt TAC
        fop = tk.Frame(self.nb, bg=BG); self.nb.add(fop, text="  ✦  Optimised  ")
        self.t_opt = make_txt(fop)

        # Assembly
        fm = tk.Frame(self.nb, bg=BG); self.nb.add(fm, text="  ▣  Assembly  ")
        self.t_asm = make_txt(fm)

    # ── Status bar ─────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=SURF2, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.lbl_status  = tk.Label(bar, text="  Ready",
                                    font=("Consolas", 9), bg=SURF2, fg=DIM,
                                    anchor="w")
        self.lbl_status.pack(side="left", fill="x", expand=True, padx=8)

        tk.Frame(bar, bg=BORDER, width=1).pack(side="right", fill="y", pady=4)
        self.lbl_cursor = tk.Label(bar, text="Ln 1  Col 1",
                                   font=("Consolas", 9), bg=SURF2, fg=DIM,
                                   anchor="e")
        self.lbl_cursor.pack(side="right", padx=14)

        tk.Frame(bar, bg=BORDER, width=1).pack(side="right", fill="y", pady=4)
        tk.Label(bar, text="SimpleLang  ·  UTF-8",
                 font=("Consolas", 9), bg=SURF2, fg=DIM2,
                 anchor="e").pack(side="right", padx=14)

    def _status(self, msg: str, colour: str = DIM):
        self.lbl_status.configure(text=f"  {msg}", fg=colour)
        self.root.update_idletasks()

    # ── Editor helpers ─────────────────────────────────────────────────────────
    def _ysync(self, *a):
        self.editor.yview(*a)
        self.gutter.yview(*a)

    def _wheel(self, e):
        d = int(-1 * (e.delta / 120))
        self.editor.yview_scroll(d, "units")
        self.gutter.yview_scroll(d, "units")
        return "break"

    def _on_key(self, _=None):
        self._refresh()

    def _refresh(self):
        self._update_gutter()
        self._highlight()
        self._update_cursor()

    def _update_gutter(self):
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        n = int(self.editor.index("end-1c").split(".")[0])
        self.gutter.insert("1.0", "\n".join(f"{i:>3}" for i in range(1, n+1)))
        self.gutter.configure(state="disabled")

    def _update_cursor(self, _=None):
        pos = self.editor.index(tk.INSERT)
        ln, col = pos.split(".")
        self.lbl_cursor.configure(text=f"Ln {ln}   Col {int(col)+1}")

    _HL = [
        ("cmt", r"//[^\n]*"),
        ("str", r'"[^"]*"'),
        ("num", r"\b\d+(\.\d+)?\b"),
        ("boo", r"\b(true|false)\b"),
        ("kw",  r"\b(int|float|bool|string|if|else|while|print)\b"),
        ("op",  r"[+\-*/%=<>!&|]+"),
    ]

    def _highlight(self):
        ed  = self.editor
        src = ed.get("1.0", "end")
        for tag, _ in self._HL:
            ed.tag_remove(tag, "1.0", "end")
        for tag, pat in self._HL:
            for m in re.finditer(pat, src):
                ed.tag_add(tag, f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # ── RUN ────────────────────────────────────────────────────────────────────
    def _run(self):
        source = self.editor.get("1.0", "end-1c").strip()
        if not source:
            self._status("⚠  Write some code first!", AMBER)
            return

        self._phases_reset()
        tv_clear(self.tv_tok)
        tv_clear(self.tv_sym)
        for t in (self.t_out, self.t_ast, self.t_tac, self.t_opt, self.t_asm):
            txt_put(t, [])

        # ── Phase 0: Lex ──────────────────────────────────────────────────────
        self._phase(0, "run"); self._status("Phase 1  —  Lexical Analysis …", ACCENT_L)
        try:
            tokens = Lexer(source).tokenize()
        except LexerError as e:
            self._phase(0, "err"); return self._err("Lexer", str(e))
        self._phase(0, "ok")

        for i, tok in enumerate(tokens, 1):
            v = repr(tok.value) if tok.value is not None else "—"
            self.tv_tok.insert("", "end", tags=(_tt_tag(tok.type),),
                               values=(i, tok.type, v, tok.line))

        # ── Phase 1: Parse ────────────────────────────────────────────────────
        self._phase(1, "run"); self._status("Phase 2  —  Parsing …", CYAN)
        try:
            ast = Parser(tokens).parse()
        except ParseError as e:
            self._phase(1, "err"); return self._err("Parser", str(e))
        self._phase(1, "ok")

        segs = [("  Abstract Syntax Tree\n", "bold_acc"),
                ("  " + "─" * 50 + "\n\n", "dm2")]
        segs += ast_segs(ast)
        txt_put(self.t_ast, segs)

        # ── Phase 2: Semantic ─────────────────────────────────────────────────
        self._phase(2, "run"); self._status("Phase 3  —  Semantic Analysis …", GREEN)
        try:
            sym = SemanticAnalyser().analyse(ast)
        except SemanticError as e:
            self._phase(2, "err"); return self._err("Semantic", str(e))
        self._phase(2, "ok")

        ttag = {"int":"ti","float":"tf","bool":"tb","string":"ts"}
        for _, sd in zip(sym._scope_names, sym._scopes):
            for s in sd.values():
                v = str(s.value) if s.value is not None else "—"
                self.tv_sym.insert("", "end",
                                   tags=(ttag.get(s.data_type, ""),),
                                   values=(s.name, s.data_type, s.scope, v))

        # ── Phase 3: TAC ──────────────────────────────────────────────────────
        self._phase(3, "run"); self._status("Phase 4  —  Generating TAC …", AMBER)
        gen = TACGenerator()
        tac = gen.generate(ast)
        render_tac(self.t_tac, tac)
        self._phase(3, "ok")

        # ── Phase 4: Optimise ─────────────────────────────────────────────────
        self._phase(4, "run"); self._status("Phase 5  —  Optimising …", PURPLE)
        opt = Optimizer().optimize(tac)
        removed = len(tac) - len(opt)
        self.t_opt.configure(state="normal")
        self.t_opt.delete("1.0", "end")
        self.t_opt.insert("end",
            f"  {len(opt)} instructions", "bold_acc")
        self.t_opt.insert("end",
            f"   ({removed} removed by optimiser)\n\n", "bold_dm")
        self.t_opt.configure(state="disabled")
        render_tac(self.t_opt, opt)
        self._phase(4, "ok")

        # ── Phase 5: Codegen ──────────────────────────────────────────────────
        self._phase(5, "run"); self._status("Phase 6  —  Code Generation …", PINK)
        cg  = CodeGenerator()
        asm = cg.generate(opt)
        render_asm(self.t_asm, asm)
        self._phase(5, "ok")

        # ── Execute ───────────────────────────────────────────────────────────
        self._status("  Running …", DIM)
        buf = io.StringIO()
        sys.stdout = buf
        try:
            VirtualMachine(asm).run()
        except Exception as e:
            sys.stdout = sys.__stdout__
            return self._err("Runtime", str(e))
        sys.stdout = sys.__stdout__

        lines  = buf.getvalue().rstrip().splitlines()
        segs   = [("  Program Output\n", "bold_acc"),
                  ("  " + "─" * 50 + "\n\n", "dm2")]
        if lines:
            for i, ln in enumerate(lines, 1):
                segs += [(f"  [{i:>2}]  ", "dm2"), (ln + "\n", "gr")]
        else:
            segs.append(("  (no output)\n", "dm"))
        segs += [("\n  " + "─" * 50 + "\n", "dm2"),
                 (f"  {len(tokens)-1} tokens  ·  "
                  f"{len(tac)} TAC  ·  "
                  f"{removed} optimised away  ·  "
                  f"{len(asm)} instructions", "dm2")]
        txt_put(self.t_out, segs)

        self.nb.select(0)
        self._status(
            f"✓  OK  ·  {len(tokens)-1} tokens  ·  "
            f"{len(tac)} TAC  ·  {removed} optimised  ·  {len(asm)} asm",
            GREEN)

    # ── error display ─────────────────────────────────────────────────────────
    def _err(self, phase: str, msg: str):
        txt_put(self.t_out, [
            (f"  ✕  {phase} Error\n", "rd"),
            ("  " + "─" * 50 + "\n\n", "dm2"),
            (msg.strip(), "am"),
        ])
        self.nb.select(0)
        self._status(f"✕  {phase} error  —  see Output tab", RED)

    # ── toolbar actions ───────────────────────────────────────────────────────
    def _clear(self):
        self.editor.delete("1.0", "end")
        self._phases_reset()
        tv_clear(self.tv_tok); tv_clear(self.tv_sym)
        for t in (self.t_out, self.t_ast, self.t_tac, self.t_opt, self.t_asm):
            txt_put(t, [])
        self._refresh()
        self._status("  Cleared")

    def _open_file(self):
        p = filedialog.askopenfilename(
            title="Open .sl file",
            filetypes=[("SimpleLang", "*.sl"), ("All files", "*.*")])
        if p:
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", open(p, encoding="utf-8").read())
            self._refresh()
            self._status(f"  Opened: {p}")

    def _save_file(self):
        p = filedialog.asksaveasfilename(
            title="Save .sl file", defaultextension=".sl",
            filetypes=[("SimpleLang", "*.sl"), ("All files", "*.*")])
        if p:
            open(p, "w", encoding="utf-8").write(
                self.editor.get("1.0", "end-1c"))
            self._status(f"  Saved: {p}", GREEN)

    def _load_example(self):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self.EXAMPLE)
        self._refresh()
        self._status("  Example loaded  —  press  ▶ RUN")


# ── entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    IDE(root)
    root.mainloop()
