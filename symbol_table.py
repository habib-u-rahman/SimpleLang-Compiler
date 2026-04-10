# =============================================================
# symbol_table.py — Symbol Table for SimpleLang Compiler
# Stores variable names, types, scopes, and memory locations
# =============================================================


class Symbol:
    """Represents a single entry in the symbol table."""

    def __init__(self, name, data_type, scope, value=None, mem_location=None):
        self.name = name
        self.data_type = data_type   # 'int' | 'float' | 'bool' | 'string'
        self.scope = scope           # 'global' or function/block name
        self.value = value           # current known value (compile-time constant)
        self.mem_location = mem_location  # e.g. 't0', 'x', offset

    def __repr__(self):
        return (f"Symbol(name={self.name!r}, type={self.data_type}, "
                f"scope={self.scope!r}, value={self.value}, mem={self.mem_location})")


class SymbolTable:
    """
    Scoped symbol table implemented as a stack of dictionaries.
    Each scope is a dict mapping identifier names to Symbol objects.
    """

    def __init__(self):
        self._scopes: list[dict[str, Symbol]] = [{}]   # start with global scope
        self._scope_names: list[str] = ["global"]

    # ------------------------------------------------------------------
    # Scope management
    # ------------------------------------------------------------------

    def enter_scope(self, name: str = "block"):
        """Push a new scope onto the stack."""
        self._scopes.append({})
        self._scope_names.append(name)

    def exit_scope(self):
        """Pop the current scope from the stack."""
        if len(self._scopes) == 1:
            raise RuntimeError("Cannot exit the global scope.")
        self._scopes.pop()
        self._scope_names.pop()

    @property
    def current_scope_name(self) -> str:
        return self._scope_names[-1]

    # ------------------------------------------------------------------
    # Insert / lookup
    # ------------------------------------------------------------------

    def insert(self, name: str, data_type: str, value=None, mem_location=None) -> Symbol:
        """Insert a new symbol into the current scope."""
        scope = self.current_scope_name
        if name in self._scopes[-1]:
            raise NameError(f"'{name}' already declared in scope '{scope}'.")
        sym = Symbol(name, data_type, scope, value, mem_location)
        self._scopes[-1][name] = sym
        return sym

    def lookup(self, name: str) -> Symbol:
        """Search for a symbol from the innermost to the outermost scope."""
        for scope_dict in reversed(self._scopes):
            if name in scope_dict:
                return scope_dict[name]
        raise NameError(f"Undeclared identifier: '{name}'.")

    def update_value(self, name: str, value):
        """Update the compile-time value of an existing symbol."""
        sym = self.lookup(name)
        sym.value = value

    def exists_in_current_scope(self, name: str) -> bool:
        return name in self._scopes[-1]

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self):
        print("\n======= Symbol Table =======")
        for scope_name, scope_dict in zip(self._scope_names, self._scopes):
            print(f"\n  Scope: {scope_name}")
            print(f"  {'Name':<15} {'Type':<10} {'Value':<15} {'Mem':<10}")
            print(f"  {'-'*50}")
            for sym in scope_dict.values():
                print(f"  {sym.name:<15} {sym.data_type:<10} "
                      f"{str(sym.value):<15} {str(sym.mem_location):<10}")
        print("============================\n")
