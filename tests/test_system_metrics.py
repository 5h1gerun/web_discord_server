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

