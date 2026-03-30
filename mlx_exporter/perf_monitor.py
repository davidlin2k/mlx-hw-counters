import time
from mlx_exporter.mcra_device import MCRADevice
from mlx_exporter.perf_counter_unit import PerfCounterUnit

class PerfMonitor:
    """Manages all performance counter units."""
 
    def __init__(self, device_path: str, units: list, counters: list):
        self.mf = MCRADevice(device_path)
        self.device_path = device_path
        self.units = {}  # name -> PerfCounterUnit
        self.counter_slots = {}  # counter_idx -> (unit_name, slot_idx)
        self.prev_values = {}  # counter_idx -> value
        self.prev_time = None
 
        # Create units and assign counters
        for idx, (unit_name, selector, metric, help_text, mtype) in enumerate(counters):
            if unit_name not in units:
                continue
            if unit_name not in self.units:
                self.units[unit_name] = PerfCounterUnit(
                    unit_name, units[unit_name], self.mf
                )
            unit = self.units[unit_name]
            slot = unit.add_counter(selector, idx)
            self.counter_slots[idx] = (unit_name, slot)
 
    def setup(self):
        """Program all units."""
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
 
    def collect(self):
        """Collect metrics. Returns list of (metric_name, labels, value, help, type) tuples."""
        now = time.time()
        values = self.sample()
        dt = now - self.prev_time if self.prev_time else None
 
        metrics = []
        for idx, (unit_name, selector, metric_name, help_text, mtype) in enumerate(COUNTERS):
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
    