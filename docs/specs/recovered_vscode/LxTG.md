# VJLive Fault Tolerance System - Runbook

## Overview

The VJLive fault tolerance system provides production-grade reliability for live performances through process isolation, automatic recovery, and safety fallback mechanisms.

## System Architecture

### Process Isolation
- **Render Engine** (`core/main.py`): OpenGL context and video output
- **Control Interface** (`gui/mixer.py` + `web_ui/`): User interaction and API
- **Media Manager** (`core/media_manager.py`): Video decoding and asset loading

### Communication
- **Shared Memory**: Frame buffers between processes
- **ZMQ/Redis**: Command/control messages
- **Unix Domain Sockets**: Low-latency heartbeats

## Recovery Strategies

### Soft Restart
- Reload effects and resume from last known state
- Maximum 3 restarts in 60 seconds
- Recovery time: <500ms

### Hard Restart
- Full process restart with state restoration
- Maximum 2 restarts in 60 seconds
- Recovery time: <2s

### Safety Mode
- Switch to fallback visuals
- Activated after too many restarts or process hangs
- Timeout: 30 seconds before hard restart

## Monitoring Service

### Supervisor Daemon
- Runs as separate process/systemd service
- Monitors heartbeats via UDP/Unix sockets
- Independent of Python GIL
- Recovery strategies and exponential backoff

### Health Monitoring
- Process health checks every 100ms
- Heartbeat timeout: 5 seconds
- Automatic restart on failure

## Plugin Sandboxing

### Effect Isolation
- Each effect wrapped in try/except
- Health scoring tracks crashes/errors
- Automatic disabling after >3 errors in 60s
- Safe mode rendering bypasses all effects

### Health Monitoring
- Monitoring interval: 5 seconds
- Error threshold: 3 errors
- Disable timeout: 300 seconds

## Safety Loop

### Failsafe Renderer
- Minimal, bulletproof rendering loop
- Pre-loaded safety video/shader
- Timeout detection: <200ms
- Seamless crossfade to safety loop

### Requirements
- Works on integrated Intel GPUs
- Minimal shader requirements
- <200ms activation time

## State Persistence

### Snapshot System
- Full application state every 5 seconds
- Includes: active clips, effect parameters, MIDI mappings
- Atomic writes to temp file + rename
- Backward compatible format

### Recovery
- "Resume Last Session" feature
- State restoration >99% accurate
- Zero data loss during ungraceful shutdown

## Configuration

### Supervisor Settings
```yaml
supervisor:
  heartbeat_port: 9999
  ipc_dir: 'ipc'
  log_dir: 'logs'
  snapshot_dir: 'snapshots'
  max_soft_restarts: 3
  max_hard_restarts: 2
  restart_window: 60
  safety_mode_timeout: 30
```

### Sandbox Settings
```yaml
sandbox:
  error_threshold: 3
  time_window: 60
  disable_timeout: 300
  monitoring_interval: 5
  log_dir: 'logs/sandbox'
```

### Safety Settings
```yaml
safety:
  timeout: 0.2
  fade_duration: 0.5
  min_frame_time: 0.016
  log_dir: 'logs/safety'
```

## Deployment

### Systemd Service
```ini
[Unit]
Description=VJLive Supervisor Daemon
After=network.target

[Service]
Type=simple
User=vjlive
ExecStart=/usr/bin/python3 /home/vjlive/vjlive/monitoring/supervisor_daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Docker Deployment
- Supervisor runs as separate container
- Shared volumes for IPC and snapshots
- Health checks integrated with Docker

## Failure Scenarios

### Plugin Crash
1. Effect throws exception
2. Sandbox catches and logs error
3. Health monitor tracks error count
4. After threshold, effect disabled
5. System continues with remaining effects

### Process Crash
1. Supervisor detects missing heartbeat
2. Process marked as unhealthy
3. Soft restart attempted
4. If fails, hard restart initiated
5. State restored from snapshot

### GPU Driver Reset
1. All processes terminate
2. Supervisor detects complete failure
3. Hard restart all processes
4. Safety loop activates during restart
5. State restored from latest snapshot

### Network Failure
1. Control interface loses connection
2. Render engine continues unaffected
3. Safety loop activates if timeout
4. Automatic recovery when network restored

## Monitoring

### Logs
- Supervisor: `logs/supervisor.log`
- Process Manager: `logs/process_manager.log`
- Sandbox: `logs/sandbox/*.log`
- Safety Loop: `logs/safety/safety_loop.log`

### Metrics
- Process uptime and restart counts
- Effect health scores
- Recovery times
- Safety mode activations

## Troubleshooting

### Common Issues

#### Supervisor Not Starting
```bash
# Check logs
journalctl -u vjlive-supervisor -f

# Verify permissions
ls -la /home/vjlive/vjlive/monitoring/supervisor_daemon.py

# Test manually
python3 /home/vjlive/vjlive/monitoring/supervisor_daemon.py
```

#### Processes Not Communicating
```bash
# Check IPC directory
ls -la /home/vjlive/vjlive/ipc/

# Verify ZMQ sockets
netstat -tlnp | grep 9999

# Check process status
ps aux | grep vjlive
```

#### Safety Loop Not Activating
```bash
# Check frame timing
journalctl -u vjlive-supervisor -f | grep "Frame timeout"

# Verify OpenGL context
glxinfo | grep "OpenGL renderer"

# Check safety logs
cat /home/vjlive/vjlive/logs/safety/safety_loop.log
```

### Recovery Procedures

#### Manual Safety Mode
```bash
# Send OSC command
oscsend localhost 9000 /vjlive/safety i 1

# Or via supervisor
supervisorctl send_command safety_mode activate
```

#### Force Restart
```bash
# Restart specific process
supervisorctl restart render_engine

# Restart all processes
supervisorctl restart all

# Full system restart
systemctl restart vjlive-supervisor
```

#### State Recovery
```bash
# List available snapshots
ls -la /home/vjlive/vjlive/snapshots/

# Restore from snapshot
python3 -c "
from core.config_manager import ConfigManager
config = ConfigManager()
config.restore_state('/path/to/snapshot.json')
"
```

## Performance Considerations

### Recovery Time Targets
- Soft restart: <500ms
- Hard restart: <2s
- Safety loop activation: <200ms
- State snapshot: async, <100ms impact

### Resource Usage
- Supervisor: <1% CPU, <10MB RAM
- Sandbox overhead: <5% CPU per effect
- Safety loop: <2% CPU, minimal GPU usage
- Snapshot storage: <100MB/hour

### Optimization Tips
- Increase monitoring interval for less critical systems
- Adjust error thresholds based on effect stability
- Use shared memory for high-bandwidth IPC
- Compress snapshots for storage efficiency

## Security Considerations

### Process Isolation
- Each process runs with minimal privileges
- IPC secured with Unix domain sockets
- No shared memory between untrusted processes

### Input Validation
- All IPC messages validated
- Effect parameters sanitized
- Configuration files verified

### Access Control
- Supervisor requires root for systemd
- Regular user for VJLive processes
- Audit logging for all recovery actions

## Maintenance

### Regular Tasks
- Monitor log files for errors
- Check snapshot directory size
- Verify process health metrics
- Update configuration as needed

### Backup Procedures
- Daily backup of snapshots
- Weekly backup of configuration
- Monthly backup of media assets

### Upgrade Process
1. Backup current state
2. Update supervisor first
3. Restart processes individually
4. Verify recovery mechanisms
5. Test with simulated failures

## Emergency Procedures

### Complete System Failure
1. Activate safety mode manually
2. Check supervisor logs for root cause
3. Restart supervisor if needed
4. Restore from latest snapshot
5. Verify all processes running

### Data Loss Prevention
- Snapshots created every 5 seconds
- Atomic writes prevent corruption
- Multiple backup locations
- Integrity checks on restore

### Performance Degradation
- Monitor CPU and memory usage
- Check effect health scores
- Verify IPC communication
- Adjust thresholds if needed

## Integration Points

### External Systems
- OSC/MIDI for manual control
- Web UI for monitoring
- External monitoring tools
- Logging aggregation systems

### APIs
- Process manager control API
- Effect health monitoring API
- State management API
- Safety loop control API

## Future Enhancements

### Planned Features
- Distributed supervisor for multi-node
- Machine learning for failure prediction
- Automated performance optimization
- Enhanced security controls

### Performance Improvements
- Faster IPC mechanisms
- More efficient snapshot compression
- Parallel recovery operations
- Predictive failure prevention

## Support

### Documentation
- API documentation
- Configuration reference
- Troubleshooting guide
- Recovery procedures

### Community
- Issue tracking
- Feature requests
- Performance reports
- Best practices sharing

---

**Last Updated**: January 31, 2026  
**Version**: 1.0  
**Author**: VJLive Engineering Team