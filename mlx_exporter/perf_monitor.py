import time
from mlx_exporter.mcra_device import MCRADevice
from mlx_exporter.perf_counter_unit import PerfCounterUnit


class PerfMonitor:
    """Manages all performance counter units."""
 
    def __init__(self, device_path: str, units: list, counters: list, setup_writes=None):
        self.mf = MCRADevice(device_path)
        self.device_path = device_path
        self.counters = counters
        self.setup_writes = setup_writes or []
        self.units = {}  # name -> PerfCounterUnit
        self.counter_slots = {}  # counter_idx -> (unit_name, slot_idx)
        self.prev_values = {}  # counter_idx -> value
        self.prev_time = None
 
        # Create units and assign counters
        for idx, (unit_name, selector, metric, help_text, mtype) in enumerate(counters):
            if unit_name not in units:
                continue
            if unit_name not in self.units:
                unit_cfg = units[unit_name]
                if isinstance(unit_cfg, int):
                    unit_cfg = {
                        "en_addr": unit_cfg,
                        "selector_addr": unit_cfg - 0x20,
                        "value_addr": unit_cfg + 0x20,
                        "start_addr": unit_cfg + 0x4,
                        "enable_bit": 0,
                        "size": 16,
                    }
                self.units[unit_name] = PerfCounterUnit(
                    unit_name,
                    unit_cfg["en_addr"],
                    self.mf,
                    selector_addr=unit_cfg.get("selector_addr"),
                    value_addr=unit_cfg.get("value_addr"),
                    start_addr=unit_cfg.get("start_addr"),
                    enable_bit=unit_cfg.get("enable_bit", 0),
                    slot_limit=unit_cfg.get("size", 16),
                )
            unit = self.units[unit_name]
            slot = unit.add_counter(selector, idx)
            self.counter_slots[idx] = (unit_name, slot)
 
    def setup(self):
        """Program all units."""
        for write in self.setup_writes:
            self.mf.write_field(
                addr=write["addr"],
                start_bit=write["start_bit"],
                size=write["size"],
                value=write["value"],
            )
        for unit in self.units.values():
            unit.program()
        time.sleep(0.1)
 
    def sample(self):
        """Read all counters. Returns dict of counter_idx -> value."""
        values = {}
        for unit in self.units.values():
            for cidx, val in unit.read_values():
                values[cidx] = val
        return values

    def debug_units(self, unit_names=None):
        """Return debug snapshots for the requested units."""
        selected_units = self.units
        if unit_names:
            selected_units = {
                name: unit for name, unit in self.units.items() if name in unit_names
            }
        return [unit.debug_snapshot() for unit in selected_units.values()]
 
    def collect(self):
        """Collect metrics. Returns list of (metric_name, labels, value, help, type) tuples."""
        now = time.time()
        values = self.sample()
        dt = now - self.prev_time if self.prev_time else None
 
        metrics = []
        for idx, (unit_name, selector, metric_name, help_text, mtype) in enumerate(self.counters):
            if idx not in values:
                continue
            val = values[idx]
            labels = f'device="{self.device_path}",unit="{unit_name}",selector="{selector}"'
 
            # Raw cumulative counter
            metrics.append((
                metric_name + "_total", labels, val,
                help_text, "counter"
            ))
 
            # Computed rate (per second)
            if dt and dt > 0 and idx in self.prev_values:
                delta = val - self.prev_values[idx]
                if delta < 0:
                    delta += 2**32  # 32-bit wraparound
                rate = delta / dt
                metrics.append((
                    metric_name + "_rate", labels, f"{rate:.2f}",
                    help_text + " (per second)", "gauge"
                ))
 
        self.prev_values = values
        self.prev_time = now
        return metrics
    
