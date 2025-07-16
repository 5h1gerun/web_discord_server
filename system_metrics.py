import os
import json
import shutil
from typing import Dict


def get_system_metrics() -> Dict[str, float]:
    """Return basic system metrics without external dependencies."""
    # Load averages may not be available on non-Unix systems
    load1 = load5 = load15 = 0.0
    if hasattr(os, "getloadavg"):
        try:
            load1, load5, load15 = os.getloadavg()
        except OSError:
            pass

    mem_total = mem_available = None
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                key, val = line.split(":", 1)
                if key == "MemTotal":
                    mem_total = int(val.strip().split()[0])
                elif key == "MemAvailable":
                    mem_available = int(val.strip().split()[0])
        if mem_total is not None and mem_available is not None:
            mem_usage_percent = 100.0 * (mem_total - mem_available) / mem_total
        else:
            mem_usage_percent = 0.0
    except FileNotFoundError:
        mem_usage_percent = 0.0

    disk = shutil.disk_usage("/")
    disk_usage_percent = 100.0 * disk.used / disk.total

    return {
        "loadavg_1min": float(load1),
        "loadavg_5min": float(load5),
        "loadavg_15min": float(load15),
        "memory_usage_percent": float(mem_usage_percent),
        "disk_usage_percent": float(disk_usage_percent),
    }


if __name__ == "__main__":
    metrics = get_system_metrics()
    print(json.dumps(metrics, indent=2))

