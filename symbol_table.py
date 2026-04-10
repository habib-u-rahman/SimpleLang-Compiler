# symbol_table.py — Symbol class for SimpleLang compiler


class Symbol:
    """Represents a single entry in the symbol table."""

    def __init__(self, name, data_type, scope, value=None, mem_location=None):
        self.name = name
        self.data_type = data_type
        self.scope = scope
        self.value = value
        self.mem_location = mem_location

    def __repr__(self):
        return (f"Symbol(name={self.name!r}, type={self.data_type}, "
                f"scope={self.scope!r}, value={self.value})")
