"""
P7-B3: Analytics Dashboard

Provides real-time performance monitoring and usage analytics for VJLive3.
Tracks CPU/GPU usage, plugin performance, memory consumption, frame rates, 
and user behavior using a local SQLite database for persistence.
"""

import sqlite3
import logging
import csv
import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from vjlive3.plugins.api import PluginBase, PluginContext

_logger = logging.getLogger("vjlive3.plugins.analytics")


@dataclass
class PerformanceMetrics:
    frame_rate: float
    latency_ms: float
    memory_usage_mb: float
    cpu_usage_pct: float
    gpu_usage_pct: float
    active_plugins: int
    plugin_id: Optional[str] = None


@dataclass
class UsageData:
    user_id: str
    event_type: str
    plugin_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceReport:
    start_time: datetime
    end_time: datetime
    avg_fps: float
    min_fps: float
    avg_latency_ms: float
    max_memory_mb: float
    avg_cpu_pct: float
    avg_gpu_pct: float
    total_samples: int


@dataclass
class UsageReport:
    start_time: datetime
    end_time: datetime
    total_events: int
    unique_users: int
    top_events: Dict[str, int]


@dataclass
class PluginPerformance:
    plugin_id: str
    avg_fps: float
    avg_latency_ms: float
    total_invocations: int


@dataclass
class UserActivity:
    user_id: str
    total_events: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    recent_events: List[Dict[str, Any]]


class AnalyticsDashboard(PluginBase):
    """
    Analytics Dashboard Integration.
    Complies with P7-B3 specifications for performance and usage tracking.
    """

    METADATA = {
        "name": "Analytics Dashboard",
        "description": "Real-time performance monitoring and usage analytics.",
        "version": "1.0.0",
        "author": "VJLive Team",
        "category": "core.business",
        "parameters": [
            {"name": "db_path", "type": "string", "default": "analytics.db"}
        ],
        "inputs": [],
        "outputs": []
    }

    def __init__(self, db_path: str = "analytics.db") -> None:
        super().__init__()
        self._db_path = db_path
        self._is_monitoring = False
        self._conn: Optional[sqlite3.Connection] = None
        
        self._init_db()

    def initialize(self, context: PluginContext) -> None:
        """Initialize parameters from context and reset connection if db_path changed."""
        super().initialize(context)
        
        param_path = self.context.get_parameter("db_path")
        if param_path and str(param_path) != self._db_path:
            self.cleanup() # Close old connection
            self._db_path = str(param_path)
            self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database and schema."""
        try:
            self._conn = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            
            cursor = self._conn.cursor()
            
            # Setup performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    frame_rate REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    memory_usage_mb REAL NOT NULL,
                    cpu_usage_pct REAL NOT NULL,
                    gpu_usage_pct REAL NOT NULL,
                    active_plugins INTEGER NOT NULL,
                    plugin_id TEXT
                )
            """)
            
            # Setup usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    plugin_id TEXT,
                    event_data TEXT
                )
            """)
            
            # Indices for quick querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_time ON performance_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_plugin ON performance_metrics(plugin_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_time ON usage_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id)")
            
            self._conn.commit()
            
        except sqlite3.Error as e:
            _logger.error("Failed to initialize analytics database: %s", e)
            self._conn = None

    def cleanup(self) -> None:
        """Cleanup database connections."""
        self.stop_monitoring()
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None
        super().cleanup()

    # ─── Monitoring State ────────────────────────────────────────────────────

    def start_monitoring(self) -> None:
        """Start accepting metrics and events."""
        if self._conn:
            self._is_monitoring = True
            _logger.info("Analytics monitoring started.")
        else:
            _logger.warning("Cannot start monitoring: database not initialized.")

    def stop_monitoring(self) -> None:
        """Stop accepting metrics and events."""
        self._is_monitoring = False
        _logger.info("Analytics monitoring stopped.")

    def is_monitoring(self) -> bool:
        """Check if metrics are currently being recorded."""
        return self._is_monitoring

    # ─── Data Recording ──────────────────────────────────────────────────────

    def record_performance(self, metrics: PerformanceMetrics) -> None:
        """Record a performance snapshot into the database."""
        if not self._is_monitoring or not self._conn:
            return
            
        now = datetime.now(timezone.utc)
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    timestamp, frame_rate, latency_ms, 
                    memory_usage_mb, cpu_usage_pct, gpu_usage_pct, 
                    active_plugins, plugin_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, metrics.frame_rate, metrics.latency_ms,
                metrics.memory_usage_mb, metrics.cpu_usage_pct, 
                metrics.gpu_usage_pct, metrics.active_plugins, 
                metrics.plugin_id
            ))
            self._conn.commit()
        except sqlite3.Error as e:
            _logger.error("Failed to record performance metric: %s", e)

    def record_usage(self, usage: UsageData) -> None:
        """Record a user usage event into the database."""
        if not self._is_monitoring or not self._conn:
            return
            
        now = datetime.now(timezone.utc)
        event_data_json = json.dumps(usage.event_data) if usage.event_data else None
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO usage_events (
                    timestamp, user_id, event_type, plugin_id, event_data
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                now, usage.user_id, usage.event_type, 
                usage.plugin_id, event_data_json
            ))
            self._conn.commit()
        except sqlite3.Error as e:
            _logger.error("Failed to record usage event: %s", e)

    # ─── Querying and Reporting ──────────────────────────────────────────────

    def get_performance_stats(self, start_time: datetime, end_time: datetime) -> PerformanceReport:
        """Aggregate performance statistics within a time window."""
        default_report = PerformanceReport(
            start_time=start_time, end_time=end_time,
            avg_fps=0.0, min_fps=0.0, avg_latency_ms=0.0, max_memory_mb=0.0,
            avg_cpu_pct=0.0, avg_gpu_pct=0.0, total_samples=0
        )
        
        if not self._conn:
            return default_report
            
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as cnt,
                    AVG(frame_rate) as avg_fps,
                    MIN(frame_rate) as min_fps,
                    AVG(latency_ms) as avg_lat,
                    MAX(memory_usage_mb) as max_mem,
                    AVG(cpu_usage_pct) as avg_cpu,
                    AVG(gpu_usage_pct) as avg_gpu
                FROM performance_metrics
                WHERE timestamp BETWEEN ? AND ?
            """, (start_time, end_time))
            
            row = cursor.fetchone()
            if row and row['cnt'] and row['cnt'] > 0:
                return PerformanceReport(
                    start_time=start_time,
                    end_time=end_time,
                    avg_fps=float(row['avg_fps']),
                    min_fps=float(row['min_fps']),
                    avg_latency_ms=float(row['avg_lat']),
                    max_memory_mb=float(row['max_mem']),
                    avg_cpu_pct=float(row['avg_cpu']),
                    avg_gpu_pct=float(row['avg_gpu']),
                    total_samples=row['cnt']
                )
        except sqlite3.Error as e:
            _logger.error("Failed to get performance stats: %s", e)
            
        return default_report

    def get_usage_stats(self, start_time: datetime, end_time: datetime) -> UsageReport:
        """Aggregate usage statistics within a time window."""
        default_report = UsageReport(
            start_time=start_time, end_time=end_time,
            total_events=0, unique_users=0, top_events={}
        )
        
        if not self._conn:
            return default_report
            
        try:
            cursor = self._conn.cursor()
            
            # Aggregates
            cursor.execute("""
                SELECT 
                    COUNT(*) as cnt,
                    COUNT(DISTINCT user_id) as unique_users
                FROM usage_events
                WHERE timestamp BETWEEN ? AND ?
            """, (start_time, end_time))
            row = cursor.fetchone()
            cnt = row['cnt'] or 0
            unique = row['unique_users'] or 0
            
            # Top events
            cursor.execute("""
                SELECT event_type, COUNT(*) as cnt
                FROM usage_events
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY event_type
                ORDER BY cnt DESC
                LIMIT 10
            """, (start_time, end_time))
            
            top_events = {r['event_type']: r['cnt'] for r in cursor.fetchall()}
            
            return UsageReport(
                start_time=start_time,
                end_time=end_time,
                total_events=cnt,
                unique_users=unique,
                top_events=top_events
            )
        except sqlite3.Error as e:
            _logger.error("Failed to get usage stats: %s", e)
            
        return default_report

    def get_plugin_performance(self, plugin_id: str) -> PluginPerformance:
        """Get performance lifetime aggregates for a specific plugin."""
        default_perf = PluginPerformance(
            plugin_id=plugin_id, avg_fps=0.0, avg_latency_ms=0.0, total_invocations=0
        )
        
        if not self._conn:
            return default_perf
            
        try:
            cursor = self._conn.cursor()
            
            # Check performance table
            cursor.execute("""
                SELECT 
                    COUNT(*) as cnt,
                    AVG(frame_rate) as avg_fps,
                    AVG(latency_ms) as avg_lat
                FROM performance_metrics
                WHERE plugin_id = ?
            """, (plugin_id,))
            
            row = cursor.fetchone()
            cnt = row['cnt'] or 0
            
            if cnt > 0:
                default_perf.avg_fps = float(row['avg_fps'])
                default_perf.avg_latency_ms = float(row['avg_lat'])
                
            # Count discrete usage invocations
            cursor.execute("""
                SELECT COUNT(*) as usages
                FROM usage_events
                WHERE plugin_id = ?
            """, (plugin_id,))
            
            usage_cnt = cursor.fetchone()['usages'] or 0
            default_perf.total_invocations = usage_cnt
            
            return default_perf
            
        except sqlite3.Error as e:
            _logger.error("Failed to get plugin performance: %s", e)
            
        return default_perf

    def get_user_activity(self, user_id: str) -> UserActivity:
        """Get activity lifetime profile for a user."""
        default_activity = UserActivity(
            user_id=user_id, total_events=0,
            first_seen=None, last_seen=None, recent_events=[]
        )
        
        if not self._conn:
            return default_activity
            
        try:
            cursor = self._conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as cnt,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM usage_events
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            cnt = row['cnt'] or 0
            
            if cnt > 0:
                default_activity.total_events = cnt
                # Sqlite3 parse_decltypes will handle the timestamp conversion natively
                # depending on the python version. If it comes back string, parse it.
                first = row['first_seen']
                last = row['last_seen']
                
                if isinstance(first, str):
                    try:
                        first = datetime.fromisoformat(first.replace('Z', '+00:00'))
                        last = datetime.fromisoformat(last.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                        
                default_activity.first_seen = first
                default_activity.last_seen = last
                
            # Recent events
            cursor.execute("""
                SELECT timestamp, event_type, plugin_id, event_data
                FROM usage_events
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            """, (user_id,))
            
            recents = []
            for r in cursor.fetchall():
                edata = {}
                if r['event_data']:
                    try:
                        edata = json.loads(r['event_data'])
                    except json.JSONDecodeError:
                        pass
                        
                # Timestamp normalization
                ts = r['timestamp']
                tstr = ts.isoformat() if isinstance(ts, datetime) else str(ts)
                
                recents.append({
                    "timestamp": tstr,
                    "event_type": r['event_type'],
                    "plugin_id": r['plugin_id'],
                    "data": edata
                })
                
            default_activity.recent_events = recents
            return default_activity
            
        except sqlite3.Error as e:
            _logger.error("Failed to get user activity: %s", e)
            
        return default_activity

    # ─── Data Export ─────────────────────────────────────────────────────────

    def export_data(self, start_time: datetime, end_time: datetime, format: str = "csv") -> str:
        """Export raw analytics data to a temporary file."""
        if format.lower() != "csv":
            raise ValueError(f"Format {format} not supported. Only 'csv' is supported.")
            
        if not self._conn:
            raise RuntimeError("Database not initialized")
            
        # Create temp file
        fd, file_path = tempfile.mkstemp(suffix=".csv", prefix="vjlive3_analytics_")
        import os
        os.close(fd)
        
        try:
            cursor = self._conn.cursor()
            
            # Export performance
            cursor.execute("""
                SELECT timestamp, frame_rate, latency_ms, memory_usage_mb, 
                       cpu_usage_pct, gpu_usage_pct, active_plugins, plugin_id
                FROM performance_metrics
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_time, end_time))
            
            perf_rows = cursor.fetchall()
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    "Type", "Timestamp", "FPS", "Latency(ms)", "Memory(MB)", 
                    "CPU(%)", "GPU(%)", "ActivePlugins", "PluginID",
                    "UserID", "EventType", "EventData"
                ])
                
                for r in perf_rows:
                    ts = r['timestamp'].isoformat() if isinstance(r['timestamp'], datetime) else str(r['timestamp'])
                    writer.writerow([
                        "PERFORMANCE", ts, r['frame_rate'], r['latency_ms'], 
                        r['memory_usage_mb'], r['cpu_usage_pct'], r['gpu_usage_pct'], 
                        r['active_plugins'], r['plugin_id'],
                        "", "", ""
                    ])
                
                # Export usage
                cursor.execute("""
                    SELECT timestamp, user_id, event_type, plugin_id, event_data
                    FROM usage_events
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start_time, end_time))
                
                usage_rows = cursor.fetchall()
                for r in usage_rows:
                    ts = r['timestamp'].isoformat() if isinstance(r['timestamp'], datetime) else str(r['timestamp'])
                    writer.writerow([
                        "USAGE", ts, "", "", "", "", "", "", r['plugin_id'],
                        r['user_id'], r['event_type'], r['event_data']
                    ])
                    
            return file_path
            
        except (sqlite3.Error, IOError) as e:
            _logger.error("Data export failed: %s", e)
            # Cleanup temp file on failure
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise RuntimeError(f"Export failed: {e}")
