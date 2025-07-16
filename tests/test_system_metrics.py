import system_metrics


def test_get_system_metrics_keys():
    metrics = system_metrics.get_system_metrics()
    required = {
        "loadavg_1min",
        "loadavg_5min",
        "loadavg_15min",
        "memory_usage_percent",
        "disk_usage_percent",
    }
    assert required <= metrics.keys()
    for key in required:
        assert isinstance(metrics[key], float)


def test_metric_ranges():
    metrics = system_metrics.get_system_metrics()
    assert 0.0 <= metrics["memory_usage_percent"] <= 100.0
    assert 0.0 <= metrics["disk_usage_percent"] <= 100.0
    assert metrics["loadavg_1min"] >= 0.0
    assert metrics["loadavg_5min"] >= 0.0
    assert metrics["loadavg_15min"] >= 0.0


def test_get_network_speed():
    speed = system_metrics.get_network_speed(0.05)
    required = {"bytes_recv_per_sec", "bytes_sent_per_sec"}
    assert required <= speed.keys()
    for key in required:
        assert isinstance(speed[key], float)
        assert speed[key] >= 0.0


def test_get_server_process_metrics():
    metrics = system_metrics.get_server_process_metrics(0.05)
    required = {"process_cpu_percent", "process_memory_rss_bytes", "open_fd_count"}
    assert required <= metrics.keys()
    assert isinstance(metrics["process_cpu_percent"], float)
    assert metrics["process_cpu_percent"] >= 0.0
    assert isinstance(metrics["process_memory_rss_bytes"], float)
    assert metrics["process_memory_rss_bytes"] >= 0.0
    assert isinstance(metrics["open_fd_count"], int)
    assert metrics["open_fd_count"] >= 0

