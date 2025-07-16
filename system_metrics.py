import os
import json
import shutil
import time
from typing import Dict, Tuple, Optional


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


def _read_net_bytes() -> Tuple[int, int]:
    """Return total received and sent bytes for non-loopback interfaces."""
    rx_total = tx_total = 0
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()[2:]
        for line in lines:
            if ':' not in line:
                continue
            iface, data = line.split(":", 1)
            iface = iface.strip()
            if iface == "lo":
                continue
            fields = data.split()
            if len(fields) >= 9:
                rx_total += int(fields[0])
                tx_total += int(fields[8])
    except FileNotFoundError:
        pass
    return rx_total, tx_total


def get_network_speed(interval: float = 1.0) -> Dict[str, float]:
    """Measure network throughput in bytes/sec over the given interval."""
    rx1, tx1 = _read_net_bytes()
    start = time.monotonic()
    time.sleep(max(interval, 0.01))
    rx2, tx2 = _read_net_bytes()
    elapsed = max(time.monotonic() - start, 0.01)
    recv_rate = max(rx2 - rx1, 0) / elapsed
    send_rate = max(tx2 - tx1, 0) / elapsed
    return {
        "bytes_recv_per_sec": float(recv_rate),
        "bytes_sent_per_sec": float(send_rate),
    }


def _read_process_times(pid: int) -> int:
    """Return user+system jiffies for the given process."""
    with open(f"/proc/{pid}/stat") as f:
        fields = f.read().split()
    utime = int(fields[13])
    stime = int(fields[14])
    return utime + stime


def _read_total_jiffies() -> int:
    """Return total jiffies for the system."""
    with open("/proc/stat") as f:
        fields = f.readline().split()[1:]
    return sum(int(x) for x in fields)


def _read_process_rss(pid: int) -> int:
    """Return RSS in bytes for the given process."""
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    return 0


def get_server_process_metrics(interval: float = 0.1, pid: Optional[int] = None) -> Dict[str, float]:
    """Return CPU and memory usage stats for this server process."""
    if pid is None:
        pid = os.getpid()
    try:
        p1 = _read_process_times(pid)
        t1 = _read_total_jiffies()
        time.sleep(max(interval, 0.01))
        p2 = _read_process_times(pid)
        t2 = _read_total_jiffies()
        cpu_percent = 0.0
        if t2 > t1:
            cpu_percent = 100.0 * (p2 - p1) / (t2 - t1)
        rss = _read_process_rss(pid)
        fd_count = len(os.listdir(f"/proc/{pid}/fd"))
    except FileNotFoundError:
        cpu_percent = 0.0
        rss = 0
        fd_count = 0
    return {
        "process_cpu_percent": float(max(cpu_percent, 0.0)),
        "process_memory_rss_bytes": float(max(rss, 0)),
        "open_fd_count": int(max(fd_count, 0)),
    }


if __name__ == "__main__":
    metrics = get_system_metrics()
    speed = get_network_speed(1.0)
    proc = get_server_process_metrics(0.1)
    metrics.update(speed)
    metrics.update(proc)
    print(json.dumps(metrics, indent=2))

