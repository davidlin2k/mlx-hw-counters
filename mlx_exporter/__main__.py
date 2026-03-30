import argparse
import glob
import os
import signal
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from mlx_exporter.perf_monitor import PerfMonitor
from mlx_exporter.mappings import cx5, cx6


CHIPS = {
    "cx5": {
        "label": "ConnectX-5",
        "source": "NVIDIA NEO-Host v2.0.10 connectx5_mcra.py",
        "units": cx5.UNITS,
        "counters": cx5.COUNTERS,
        "setup_writes": [],
    },
    "cx6": {
        "label": "ConnectX-6",
        "source": "NVIDIA NEO-Host connectx6_mcra.py",
        "units": cx6.UNITS,
        "counters": cx6.COUNTERS,
        "setup_writes": cx6.SETUP_WRITES,
    },
}


def format_prometheus(metrics, chip_label, source_label):
    """Format metrics as Prometheus text exposition."""
    lines = [
        f"# {chip_label} NIC-internal performance counters via MCRA",
        f"# Source: {source_label}",
        ""
    ]
 
    seen_metrics = set()
    for name, labels, value, help_text, prom_type in metrics:
        if name not in seen_metrics:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {prom_type}")
            seen_metrics.add(name)
        lines.append(f"{name}{{{labels}}} {value}")
 
    lines.append("")
    return "\n".join(lines)


def format_unit_debug(snapshots):
    """Format unit register snapshots for human inspection."""
    lines = []
    for snapshot in snapshots:
        lines.append(f"[{snapshot['name']}]")
        en_addr, en_val = snapshot["enable_reg"]
        lines.append(
            f"enable  0x{en_addr:06x} = 0x{en_val:08x} "
            f"(bit {snapshot['enable_bit']})"
        )

        if snapshot["start_reg"] is not None:
            start_addr, start_val = snapshot["start_reg"]
            lines.append(f"start   0x{start_addr:06x} = 0x{start_val:08x}")

        for addr, val in snapshot["selector_regs"]:
            lines.append(f"select  0x{addr:06x} = 0x{val:08x}")

        for slot, (selector, _) in enumerate(snapshot["selectors"]):
            addr, val = snapshot["value_regs"][slot]
            lines.append(
                f"value   slot={slot:02d} selector={selector:03d} "
                f"addr=0x{addr:06x} value=0x{val:08x} ({val})"
            )

        lines.append("")
    return "\n".join(lines)


class MetricsHandler(BaseHTTPRequestHandler):
    monitor = None
    chip = None
 
    def do_GET(self):
        if self.path == "/metrics":
            metrics = self.monitor.collect()
            body = format_prometheus(
                metrics,
                self.chip["label"],
                self.chip["source"],
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            body = b"<html><body><a href='/metrics'>Metrics</a></body></html>"
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)
 
    def log_message(self, format, *args):
        pass  # Suppress request logging
 

def find_device():
    """Find the MST device path."""
    # CX-5 PCI device ID
    for pattern in ["/dev/mst/*_pciconf*"]:
        devices = sorted(glob.glob(pattern))
        if devices:
            return devices[0]
    return None
 
def main():
    parser = argparse.ArgumentParser(description="Mellanox/NVIDIA MCRA Prometheus exporter")
    parser.add_argument(
        "--chip",
        choices=sorted(CHIPS),
        default="cx5",
        help="Counter map to use (default: cx5)",
    )
    parser.add_argument("-d", "--device", help="MST device path (auto-detect if omitted)")
    parser.add_argument("-o", "--output", default="/var/lib/prometheus/node-exporter/mlx5_perf.prom",
                        help="Textfile output path")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Poll interval (seconds)")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=9550, help="HTTP port (default: 9550)")
    parser.add_argument("--once", action="store_true", help="Single collection to stdout")
    parser.add_argument(
        "--dump-unit",
        action="append",
        metavar="UNIT",
        help="Dump live selector/value registers for a unit after setup; may be passed multiple times",
    )
    args = parser.parse_args()
 
    device = args.device or find_device()
    if not device:
        print("ERROR: No MST device found. Run 'mst start' first.", file=sys.stderr)
        sys.exit(1)

    chip = CHIPS[args.chip]
 
    monitor = PerfMonitor(
        device,
        chip["units"],
        chip["counters"],
        setup_writes=chip["setup_writes"],
    )
    monitor.setup()
 
    print(
        f"mlx_mcra_exporter: chip={args.chip} device={device}",
        file=sys.stderr,
    )
    print(
        f"mlx_mcra_exporter: {len(chip['counters'])} counters across {len(monitor.units)} units",
        file=sys.stderr,
    )

    if args.dump_unit:
        print(format_unit_debug(monitor.debug_units(set(args.dump_unit))))
        return
 
    if args.once:
        metrics = monitor.collect()
        print(format_prometheus(metrics, chip["label"], chip["source"]))
        return
 
    if args.http:
        MetricsHandler.monitor = monitor
        MetricsHandler.chip = chip
        server = HTTPServer(("", args.port), MetricsHandler)
        print(f"mlx_mcra_exporter: HTTP server on :{args.port}/metrics", file=sys.stderr)
        signal.signal(signal.SIGTERM, lambda *a: (server.shutdown(), sys.exit(0)))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return
 
    # Textfile collector mode
    print(f"mlx_mcra_exporter: polling every {args.interval}s -> {args.output}", file=sys.stderr)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
 
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    try:
        while True:
            metrics = monitor.collect()
            body = format_prometheus(metrics, chip["label"], chip["source"])
            tmp = f"{args.output}.tmp.{os.getpid()}"
            with open(tmp, "w") as f:
                f.write(body)
            os.rename(tmp, args.output)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
 
 
if __name__ == "__main__":
    main()
