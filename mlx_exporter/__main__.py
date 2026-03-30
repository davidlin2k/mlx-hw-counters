import argparse
import glob
import os
import signal
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from mlx_exporter.perf_monitor import PerfMonitor
from mlx_exporter.mappings.cx5 import COUNTERS, UNITS


def format_prometheus(metrics):
    """Format metrics as Prometheus text exposition."""
    lines = [
        "# ConnectX-5 NIC-internal performance counters via MCRA",
        "# Source: NVIDIA NEO-Host v2.0.10 connectx5_mcra.py",
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
 

class MetricsHandler(BaseHTTPRequestHandler):
    monitor = None
 
    def do_GET(self):
        if self.path == "/metrics":
            metrics = self.monitor.collect()
            body = format_prometheus(metrics).encode()
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
    parser = argparse.ArgumentParser(description="ConnectX-5 MCRA Prometheus exporter")
    parser.add_argument("-d", "--device", help="MST device path (auto-detect if omitted)")
    parser.add_argument("-o", "--output", default="/var/lib/prometheus/node-exporter/mlx5_perf.prom",
                        help="Textfile output path")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Poll interval (seconds)")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=9550, help="HTTP port (default: 9550)")
    parser.add_argument("--once", action="store_true", help="Single collection to stdout")
    args = parser.parse_args()
 
    device = args.device or find_device()
    if not device:
        print("ERROR: No MST device found. Run 'mst start' first.", file=sys.stderr)
        sys.exit(1)
 
    monitor = PerfMonitor(device)
    monitor.setup()
 
    print(f"mlx5_mcra_exporter: device={device}", file=sys.stderr)
    print(f"mlx5_mcra_exporter: {len(COUNTERS)} counters across {len(monitor.units)} units", file=sys.stderr)
 
    if args.once:
        metrics = monitor.collect()
        print(format_prometheus(metrics))
        return
 
    if args.http:
        MetricsHandler.monitor = monitor
        server = HTTPServer(("", args.port), MetricsHandler)
        print(f"mlx5_mcra_exporter: HTTP server on :{args.port}/metrics", file=sys.stderr)
        signal.signal(signal.SIGTERM, lambda *a: (server.shutdown(), sys.exit(0)))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return
 
    # Textfile collector mode
    print(f"mlx5_mcra_exporter: polling every {args.interval}s -> {args.output}", file=sys.stderr)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
 
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    try:
        while True:
            metrics = monitor.collect()
            body = format_prometheus(metrics)
            tmp = f"{args.output}.tmp.{os.getpid()}"
            with open(tmp, "w") as f:
                f.write(body)
            os.rename(tmp, args.output)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
 
 
if __name__ == "__main__":
    main()