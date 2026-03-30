import subprocess

class MCRADevice:
    """Direct CR-space read/write via mcra command."""
 
    def __init__(self, device_path: str):
        self.device = device_path
 
    def read(self, addr: int) -> int:
        """Read a 32-bit register. Returns integer."""
        result = subprocess.run(
            ["mcra", self.device, f"0x{addr:06x}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError(f"mcra read 0x{addr:06x} failed: {result.stderr}")
        return int(result.stdout.strip(), 16)
 
    def write(self, addr, value):
        """Write a 32-bit register."""
        result = subprocess.run(
            ["mcra", self.device, f"0x{addr:06x}", f"0x{value:08x}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError(f"mcra write 0x{addr:06x} failed: {result.stderr}")
 
    def read_block(self, base_addr, count):
        """Read consecutive 32-bit registers. Returns list of ints."""
        values = []
        for i in range(count):
            values.append(self.read(base_addr + i * 4))
        return values
    