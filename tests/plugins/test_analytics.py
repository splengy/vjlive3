"""
Tests for P7-B3 Analytics Dashboard.
"""

import pytest
import os
import sqlite3
import csv
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from vjlive3.plugins.analytics import (
    AnalyticsDashboard, PerformanceMetrics, UsageData
)
from vjlive3.plugins.api import PluginContext

# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def memory_db():
    return ":memory:"

@pytest.fixture
def analytics(memory_db):
    dashboard = AnalyticsDashboard(db_path=memory_db)
    return dashboard

@pytest.fixture
def now():
    return datetime.now(timezone.utc)

# ─── Tests ─────────────────────────────────────────────────────────────

def test_init_no_hardware(analytics, memory_db):
    """Module starts without crashing and handles database connections."""
    assert analytics.METADATA["name"] == "Analytics Dashboard"
    assert analytics._db_path == memory_db
    assert analytics._conn is not None
    
    # Test initialize param inheritance
    ctx = MagicMock(spec=PluginContext)
    ctx.get_parameter.return_value = "new_db.sqlite"
    
    # Needs to not crash
    analytics.initialize(ctx)
    assert analytics._db_path == "new_db.sqlite"
    
    # Manual rollback of file
    if os.path.exists("new_db.sqlite"):
        os.remove("new_db.sqlite")

def test_monitoring_start_stop(analytics):
    """Starts and stops monitoring."""
    assert analytics.is_monitoring() is False
    
    analytics.start_monitoring()
    assert analytics.is_monitoring() is True
    
    analytics.stop_monitoring()
    assert analytics.is_monitoring() is False
    
    analytics._conn = None
    analytics.start_monitoring()
    assert analytics.is_monitoring() is False

def test_performance_recording(analytics):
    """Records performance metrics."""
    analytics.start_monitoring()
    
    metric = PerformanceMetrics(
        frame_rate=60.0,
        latency_ms=16.6,
        memory_usage_mb=1024.0,
        cpu_usage_pct=25.0,
        gpu_usage_pct=45.0,
        active_plugins=2,
        plugin_id="my_plugin"
    )
    
    analytics.record_performance(metric)
    
    # Bypass logic if missing DB
    analytics._conn = None
    analytics.record_performance(metric)  # Should not crash

def test_usage_recording(analytics):
    """Records usage data."""
    analytics.start_monitoring()
    
    usage = UsageData(
        user_id="user1",
        event_type="app_opened",
        plugin_id=None,
        event_data={"resolution": "1080p"}
    )
    
    analytics.record_usage(usage)
    
    analytics._conn = None
    analytics.record_usage(usage)  # Should not crash

def test_performance_query(analytics, now):
    """Queries performance data."""
    analytics.start_monitoring()
    
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)
    
    # Record two samples
    m1 = PerformanceMetrics(60.0, 10.0, 100.0, 10.0, 20.0, 1, "plug1")
    m2 = PerformanceMetrics(30.0, 20.0, 200.0, 20.0, 40.0, 1, "plug1")
    analytics.record_performance(m1)
    analytics.record_performance(m2)
    
    report = analytics.get_performance_stats(start, end)
    
    assert report.total_samples == 2
    assert report.avg_fps == 45.0
    assert report.min_fps == 30.0
    assert report.max_memory_mb == 200.0
    
    analytics._conn = None
    empty = analytics.get_performance_stats(start, end)
    assert empty.total_samples == 0

def test_usage_query(analytics, now):
    """Queries usage data."""
    analytics.start_monitoring()
    
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)
    
    analytics.record_usage(UsageData("user1", "click"))
    analytics.record_usage(UsageData("user2", "click"))
    analytics.record_usage(UsageData("user1", "scroll"))
    
    report = analytics.get_usage_stats(start, end)
    
    assert report.total_events == 3
    assert report.unique_users == 2
    assert report.top_events["click"] == 2
    assert report.top_events["scroll"] == 1
    
    analytics._conn = None
    empty = analytics.get_usage_stats(start, end)
    assert empty.total_events == 0

def test_plugin_and_user_queries(analytics, now):
    """Queries for specific plugin and user activity."""
    analytics.start_monitoring()
    
    m1 = PerformanceMetrics(60.0, 10.0, 100.0, 10.0, 20.0, 1, "plug_x")
    analytics.record_performance(m1)
    analytics.record_usage(UsageData("user1", "click", "plug_x"))
    
    # Plugin perf
    plug_perf = analytics.get_plugin_performance("plug_x")
    assert plug_perf.avg_fps == 60.0
    assert plug_perf.total_invocations == 1
    
    # User perf
    user_act = analytics.get_user_activity("user1")
    assert user_act.total_events == 1
    assert user_act.first_seen is not None
    assert len(user_act.recent_events) == 1
    assert user_act.recent_events[0]["plugin_id"] == "plug_x"
    
    analytics._conn = None
    assert analytics.get_plugin_performance("x").total_invocations == 0
    assert analytics.get_user_activity("x").total_events == 0

def test_data_export(analytics, now):
    """Exports data correctly to CSV."""
    analytics.start_monitoring()
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)
    
    analytics.record_usage(UsageData("u1", "click", "p1", {"meta": 1}))
    analytics.record_performance(PerformanceMetrics(60.0, 10.0, 10.0, 10.0, 10.0, 1, "p1"))
    
    csv_path = analytics.export_data(start, end, format="csv")
    
    assert os.path.exists(csv_path)
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        # Header + 1 Perf + 1 Usage = 3 lines
        assert len(rows) == 3
        
    os.remove(csv_path)
    
    # Format error
    with pytest.raises(ValueError):
        analytics.export_data(start, end, format="xml")
        
    # Bad connection
    analytics._conn = None
    with pytest.raises(RuntimeError):
        analytics.export_data(start, end, format="csv")

@patch("sqlite3.connect")
def test_edge_cases(mock_connect, analytics, now):
    """Handles errors gracefully."""
    # Insert with bad data mimicking SQL type error internally
    
    # SQLite error handler catching
    # Creating a mock connection
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = sqlite3.Error("Mocked DB error")
    mock_connect.return_value = mock_conn
    
    analytics.cleanup()
    analytics._db_path = ":memory:" # reset
    analytics._init_db() # Uses the mock connect
    analytics.start_monitoring()
    
    # these shouldn't crash
    analytics.record_usage(UsageData("u", "c"))
    analytics.record_performance(PerformanceMetrics(1,1,1,1,1,1))
    
    # Reports should return defaults and not crash
    assert analytics.get_usage_stats(now, now).total_events == 0
    assert analytics.get_performance_stats(now, now).total_samples == 0
    assert analytics.get_plugin_performance("p").avg_fps == 0
    assert analytics.get_user_activity("u").total_events == 0
    
    with pytest.raises(RuntimeError):
        analytics.export_data(now, now)
        
    analytics.cleanup()
    
def test_json_decode_edge_cases(now):
    analytics2 = AnalyticsDashboard(db_path=":memory:")
    analytics2.start_monitoring()
    
    # JSON decode error in user activity
    cursor = analytics2._conn.cursor()
    cursor.execute("INSERT INTO usage_events (timestamp, user_id, event_type, event_data) VALUES (?, ?, ?, ?)",
                  (now, "json_u", "click", "BADJSON{"))
    analytics2._conn.commit()
    
    user_act = analytics2.get_user_activity("json_u")
    assert user_act.recent_events[0]["data"] == {} # defaulted gracefully
    
    analytics2.cleanup()
