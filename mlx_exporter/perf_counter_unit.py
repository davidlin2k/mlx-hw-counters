class PerfCounterUnit:
    """Manages one NIC functional unit's performance counter block."""
 
    def __init__(
        self,
        name,
        en_addr,
        mf,
        selector_addr=None,
        value_addr=None,
        start_addr=None,
        enable_bit=0,
        slot_limit=16,
    ):
        self.name = name
        self.en_addr = en_addr
        self.sel_addr = selector_addr if selector_addr is not None else en_addr - 0x20
        self.val_addr = value_addr if value_addr is not None else en_addr + 0x20
        self.start_addr = start_addr
        self.enable_bit = enable_bit
        self.mf = mf
        self.selectors = []  # list of (selector_value, counter_index_in_COUNTERS)
        self.slot_count = 0
        self.slot_limit = slot_limit
 
    def add_counter(self, selector, counter_idx):
        """Add a counter with given selector. Returns slot index."""
        slot = self.slot_count
        if slot >= self.slot_limit:
            raise RuntimeError(
                f"Unit {self.name}: too many counters (max {self.slot_limit})"
            )
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

        # Some units expose a start-mask register immediately after the enable
        # register. When present, arm one bit per programmed counter slot.
        if self.start_addr is not None and self.slot_count:
            self.mf.write(self.start_addr, (1 << self.slot_count) - 1)

        # Enable the unit using the documented enable bit.
        current = self.mf.read(self.en_addr)
        self.mf.write(self.en_addr, current | (1 << self.enable_bit))

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
            "start_reg": None if self.start_addr is None else (
                self.start_addr, self.mf.read(self.start_addr)
            ),
            "enable_bit": self.enable_bit,
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
 
