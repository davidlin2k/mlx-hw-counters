
class PerfCounterUnit:
    """Manages one NIC functional unit's performance counter block."""
 
    def __init__(self, name, en_addr, mf):
        self.name = name
        self.en_addr = en_addr
        self.sel_addr = en_addr - 0x20
        self.val_addr = en_addr + 0x20
        self.mf = mf
        self.selectors = []  # list of (selector_value, counter_index_in_COUNTERS)
        self.slot_count = 0
 
    def add_counter(self, selector, counter_idx):
        """Add a counter with given selector. Returns slot index."""
        slot = self.slot_count
        if slot >= 16:
            raise RuntimeError(f"Unit {self.name}: too many counters (max 16)")
        self.selectors.append((selector, counter_idx))
        self.slot_count += 1
        return slot
 
    def program(self):
        """Write selector registers and enable the unit."""
        # Pack selectors in pairs: even-index in high 16 bits, odd in low 16 bits
        num_words = (self.slot_count + 1) // 2
        for w in range(num_words):
            s0 = self.selectors[w * 2][0] if w * 2 < self.slot_count else 0
            s1 = self.selectors[w * 2 + 1][0] if w * 2 + 1 < self.slot_count else 0
            packed = (s0 << 16) | s1
            self.mf.write(self.sel_addr + w * 4, packed)
 
        # Enable
        self.mf.write(self.en_addr, 1)

    def debug_snapshot(self):
        """Return current programming and sampled register values for this unit."""
        num_words = (self.slot_count + 1) // 2
        selector_regs = []
        value_regs = []

        for w in range(num_words):
            addr = self.sel_addr + w * 4
            selector_regs.append((addr, self.mf.read(addr)))

        for slot in range(self.slot_count):
            addr = self.val_addr + slot * 4
            value_regs.append((addr, self.mf.read(addr)))

        return {
            "name": self.name,
            "enable_reg": (self.en_addr, self.mf.read(self.en_addr)),
            "selector_regs": selector_regs,
            "value_regs": value_regs,
            "selectors": list(self.selectors),
        }

    def read_values(self):
        """Read all counter values. Returns list of (counter_idx, value) tuples."""
        results = []
        for slot, (sel, cidx) in enumerate(self.selectors):
            val = self.mf.read(self.val_addr + slot * 4)
            results.append((cidx, val))
        return results
 
