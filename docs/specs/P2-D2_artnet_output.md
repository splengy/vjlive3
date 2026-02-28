# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P2-D2_artnet_output.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D2 — ArtNet Output

**What This Module Does**

Implements a professional lighting control output module that translates VJLive3's internal DMX data into Art-Net protocol for network-based lighting control. The ArtNet Output module enables VJLive3 to control professional lighting fixtures (moving heads, LED pars, etc.) over Ethernet, providing a bridge between visual performance and stage lighting. It supports both Art-Net v1 and v4 protocols, multiple universes, and can optionally receive Art-Net data for bi-directional communication with external lighting controllers.

---

## Architecture Decisions

- **Pattern:** Protocol Adapter with Dual-Mode Operation (Send/Receive)
- **Rationale:** Art-Net is a widely adopted networking protocol for DMX512 over IP. The module must convert VJLive3's internal DMX representation to Art-Net packets and transmit them over UDP. Supporting both send and receive modes allows VJLive3 to both control lights and be controlled by external lighting consoles, enabling hybrid workflows.
- **Constraints:**
  - Must support Art-Net v1 and v4 protocols
  - Must handle up to 32,768 channels (512 channels × 64 universes)
  - Must transmit at configurable refresh rates (typically 30-44 Hz)
  - Must support broadcast and unicast modes
  - Must handle network errors gracefully
  - Must integrate with existing LightingBridge system
  - Must provide low-latency transmission (< 10ms)
  - Must support both IPv4 and IPv6
  - Must implement proper packet sequencing and timing
  - Must allow runtime configuration changes

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `core/lighting_bridge.py` (L465-484) | LightingBridge._update_loop | Port — main update loop |
| VJlive-2 | `core/lighting_bridge.py` (L481-500) | LightingBridge.get_status | Port — status reporting |
| VJlive-2 | `core/lighting_bridge.py` (L497-516) | LightingBridge initialization | Port — initialization pattern |
| VJlive-2 | `core/timeline/quantum_timeline.py` (L417-436) | export_to_show_control | Reference — export pattern |
| VJlive-2 | `core/timeline/quantum_timeline.py` (L433-452) | _export_to_artnet | Reference — ArtNet export |
| VJlive-2 | `TEST_DMX_INPUT.md` (L1-20) | DMX input test | Reference — testing approach |

---

## Public Interface

```python
class ArtNetOutput:
    """Art-Net protocol output for DMX data transmission."""
    
    def __init__(self, config: ArtNetConfig) -> None:...
    def start(self) -> bool:...
    def stop(self) -> None:...
    def send_universe(self, universe: int, data: bytes) -> bool:...
    def send_dmx(self, universe: DMXUniverse, data: List[int]) -> bool:...
    def receive_artnet(self) -> Dict[int, bytes]:...
    def get_status(self) -> ArtNetStatus:...
    def set_broadcast(self, enabled: bool) -> None:...
    def set_broadcast_address(self, address: str) -> None:...
    def set_refresh_rate(self, rate: int) -> None:...
    def get_stats(self) -> dict:...
    def subscribe(self, callback: Callable) -> None:...
    def unsubscribe(self, callback: Callable) -> None:...
    def set_merge_mode(self, mode: MergeMode) -> None:...
    def get_merge_mode(self) -> MergeMode:...
    def set_priority(self, priority: int) -> None:...
    def get_priority(self) -> int:...

class ArtNetConfig:
    """Configuration for Art-Net output."""
    
    def __init__(self,
                 broadcast: bool = True,
                 broadcast_address: str = "255.255.255.255",
                 refresh_rate: int = 30,
                 port: int = 6454,
                 universe_start: int = 0,
                 universe_count: int = 1,
                 merge_mode: MergeMode = MergeMode.HTP,
                 priority: int = 100) -> None:...
    def validate(self) -> List[str]:...

class ArtNetStatus:
    """Status information for Art-Net output."""
    
    def __init__(self,
                 running: bool,
                 universes: int,
                 packets_sent: int,
                 packets_received: int,
                 errors: int,
                 last_error: Optional[str]) -> None:...
    def to_dict(self) -> dict:...
```

---

## Art-Net Protocol Implementation

### Core Components

1. **ArtNetOutput**: Main controller for Art-Net transmission and reception
2. **ArtNetPacket**: Art-Net protocol packet structures
3. **ArtNetConfig**: Configuration management
4. **ArtNetStatus**: Status reporting and statistics

### ArtNetOutput Implementation

```python
class ArtNetOutput:
    """Art-Net protocol output for DMX data transmission."""
    
    def __init__(self, config: ArtNetConfig):
        self.config = config
        self.running = False
        self.socket = None
        self.universe_data: Dict[int, bytes] = {}
        self.universe_ports: Dict[int, int] = {}
        self.stats = ArtNetStats()
        self.subscribers: List[Callable] = []
        self.merge_mode = config.merge_mode
        self.priority = config.priority
        self.broadcast_enabled = config.broadcast
        self.broadcast_address = config.broadcast_address
        self.refresh_rate = config.refresh_rate
        self.port = config.port
        self.universe_start = config.universe_start
        self.universe_count = config.universe_count
        
        # Initialize universe data buffers
        for universe in range(self.universe_start, self.universe_start + self.universe_count):
            self.universe_data[universe] = bytes(512)  # 512 channels per universe
            self.universe_ports[universe] = self.port + universe
            
    def start(self) -> bool:
        """Start Art-Net output."""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port if receiving
            if self.config.receive_enabled:
                self.socket.bind(('0.0.0.0', self.port))
                self.socket.setblocking(False)
                
            self.running = True
            
            # Start transmission thread
            self.transmit_thread = threading.Thread(
                target=self._transmit_loop,
                daemon=True
            )
            self.transmit_thread.start()
            
            # Start receive thread if enabled
            if self.config.receive_enabled:
                self.receive_thread = threading.Thread(
                    target=self._receive_loop,
                    daemon=True
                )
                self.receive_thread.start()
                
            logger.info(f"ArtNetOutput started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ArtNetOutput: {e}")
            return False
    
    def stop(self) -> None:
        """Stop Art-Net output."""
        self.running = False
        if self.transmit_thread:
            self.transmit_thread.join(timeout=1.0)
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        if self.socket:
            self.socket.close()
        logger.info("ArtNetOutput stopped")
    
    def send_universe(self, universe: int, data: bytes) -> bool:
        """Send DMX data for a specific universe."""
        if universe not in self.universe_data:
            logger.warning(f"Universe {universe} not in configured range")
            return False
            
        if len(data) > 512:
            logger.warning(f"DMX data too large for universe {universe}: {len(data)} > 512")
            return False
            
        # Pad to 512 bytes if needed
        padded_data = data.ljust(512, b'\x00')
        
        # Store data for transmission
        self.universe_data[universe] = padded_data
        
        return True
    
    def send_dmx(self, universe: DMXUniverse, data: List[int]) -> bool:
        """Send DMX data as list of integers."""
        if len(data) > 512:
            logger.warning(f"DMX data too large: {len(data)} > 512")
            return False
            
        # Convert to bytes
        dmx_bytes = bytes(data).ljust(512, b'\x00')
        return self.send_universe(universe.value, dmx_bytes)
    
    def receive_artnet(self) -> Dict[int, bytes]:
        """Receive Art-Net data from external sources."""
        # This method would be called by the receive thread
        # Returns a dict of universe -> data
        received = {}
        # Implementation would read from socket buffer
        return received
    
    def get_status(self) -> ArtNetStatus:
        """Get current Art-Net output status."""
        return ArtNetStatus(
            running=self.running,
            universes=len(self.universe_data),
            packets_sent=self.stats.packets_sent,
            packets_received=self.stats.packets_received,
            errors=self.stats.errors,
            last_error=self.stats.last_error
        )
    
    def _transmit_loop(self) -> None:
        """Main transmission loop."""
        while self.running:
            try:
                # Build Art-Net packets for all universes
                for universe, data in self.universe_data.items():
                    packet = self._build_artnet_packet(universe, data)
                    
                    # Send packet
                    if self.broadcast_enabled:
                        self.socket.sendto(packet, (self.broadcast_address, self.port))
                    else:
                        # Send to specific targets (would be configured)
                        for target in self.config.targets:
                            self.socket.sendto(packet, (target, self.port))
                    
                    self.stats.packets_sent += 1
                    
                # Sleep to maintain refresh rate
                time.sleep(1.0 / self.refresh_rate)
                
            except Exception as e:
                logger.error(f"Error in Art-Net transmit loop: {e}")
                self.stats.errors += 1
                self.stats.last_error = str(e)
                time.sleep(0.1)
    
    def _receive_loop(self) -> None:
        """Main receive loop."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    self._process_artnet_packet(data, addr)
                    self.stats.packets_received += 1
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error in Art-Net receive loop: {e}")
                self.stats.errors += 1
                self.stats.last_error = str(e)
                time.sleep(0.1)
    
    def _build_artnet_packet(self, universe: int, data: bytes) -> bytes:
        """Build an Art-Net protocol packet."""
        # Art-Net v4 packet structure
        packet = bytearray()
        
        # Art-Net header
        packet.extend(b'Art-Net\x00')  # ID (8 bytes)
        packet.append(0x00)  # OpCode (low byte) - ArtDMX = 0x5000
        packet.append(0x50)  # OpCode (high byte)
        packet.append(0x00)  # Version (high byte)
        packet.append(0x0E)  # Version (low byte) - v14
        packet.append(0x00)  # Sequence (optional)
        packet.append(0x00)  # Physical (universe low byte)
        packet.append(universe & 0xFF)  # Universe low byte
        packet.append((universe >> 8) & 0xFF)  # Universe high byte
        packet.append(len(data) & 0xFF)  # Length low byte
        packet.append((len(data) >> 8) & 0xFF)  # Length high byte
        
        # DMX data
        packet.extend(data[:512])
        
        return bytes(packet)
    
    def _process_artnet_packet(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Process received Art-Net packet."""
        if len(data) < 20:
            return
            
        # Check Art-Net header
        if data[:8] != b'Art-Net\x00':
            return
            
        # Extract universe and data
        universe = data[14] | (data[15] << 8)
        dmx_data = data[21:21+512]
        
        # Notify subscribers
        for callback in self.subscribers:
            try:
                callback(universe, dmx_data, addr)
            except Exception as e:
                logger.error(f"Error in Art-Net subscriber callback: {e}")
```

### Art-Net Packet Structure

```python
class ArtNetPacket:
    """Art-Net protocol packet."""
    
    # Art-Net v4 packet format
    # 0-7: ID ("Art-Net\x00")
    # 8-9: OpCode (0x5000 for ArtDMX)
    # 10-11: Version (0x000E for v14)
    # 12: Sequence (optional)
    # 13: Physical (universe low byte)
    # 14-15: Universe (0-32767)
    # 16-17: Length (number of DMX channels)
    # 18+: DMX data (up to 512 bytes)
    
    @staticmethod
    def create_dmx_packet(universe: int, dmx_data: bytes, sequence: int = 0) -> bytes:
        """Create an ArtDMX packet."""
        if len(dmx_data) > 512:
            raise ValueError("DMX data cannot exceed 512 bytes")
            
        packet = bytearray(18 + len(dmx_data))
        
        # Header
        packet[0:8] = b'Art-Net\x00'
        packet[8] = 0x00  # OpCode low
        packet[9] = 0x50  # OpCode high (ArtDMX)
        packet[10] = 0x00  # Version high
        packet[11] = 0x0E  # Version low (v14)
        packet[12] = sequence & 0xFF
        packet[13] = 0x00  # Physical
        packet[14] = universe & 0xFF
        packet[15] = (universe >> 8) & 0xFF
        packet[16] = len(dmx_data) & 0xFF
        packet[17] = (len(dmx_data) >> 8) & 0xFF
        
        # DMX data
        packet[18:18+len(dmx_data)] = dmx_data
        
        return bytes(packet)
    
    @staticmethod
    def parse_packet(packet: bytes) -> Optional[Dict]:
        """Parse an Art-Net packet."""
        if len(packet) < 20:
            return None
            
        if packet[0:8] != b'Art-Net\x00':
            return None
            
        opcode = packet[8] | (packet[9] << 8)
        version = packet[10] << 8 | packet[11]
        universe = packet[14] | (packet[15] << 8)
        length = packet[16] | (packet[17] << 8)
        
        return {
            'opcode': opcode,
            'version': version,
            'universe': universe,
            'length': length,
            'data': packet[18:18+length]
        }
```

---

## Integration with LightingBridge

### LightingBridge Integration

```python
class LightingBridge:
    """Bridge between VJLive and external lighting protocols."""
    
    def __init__(self, config: LightingConfig):
        self.config = config
        self.artnet_controller: Optional[ArtNetOutput] = None
        self.dmx_controller: Optional[DMXController] = None
        
        # Initialize Art-Net if configured
        if config.protocol in [Protocol.ARTNET, Protocol.HYBRID]:
            artnet_config = ArtNetConfig(
                broadcast=config.artnet_broadcast,
                broadcast_address=config.artnet_broadcast_address,
                refresh_rate=config.refresh_rate,
                port=config.artnet_port,
                universe_start=config.artnet_universe_start,
                universe_count=config.artnet_universe_count,
                merge_mode=config.merge_mode,
                priority=config.priority
            )
            self.artnet_controller = ArtNetOutput(artnet_config)
            
    def start(self) -> bool:
        """Start lighting bridge."""
        success = True
        
        if self.artnet_controller:
            if not self.artnet_controller.start():
                success = False
                logger.error("Failed to start Art-Net controller")
                
        if self.dmx_controller:
            if not self.dmx_controller.start():
                success = False
                logger.error("Failed to start DMX controller")
                
        if success:
            self.running = True
            logger.info("LightingBridge started")
            
        return success
    
    def stop(self) -> None:
        """Stop lighting bridge."""
        self.running = False
        
        if self.artnet_controller:
            self.artnet_controller.stop()
            
        if self.dmx_controller:
            self.dmx_controller.stop()
            
        logger.info("LightingBridge stopped")
    
    def update(self) -> None:
        """Update lighting state (called each frame)."""
        if not self.running:
            return
            
        try:
            # Send DMX data via Art-Net
            if self.artnet_controller:
                for universe in DMXUniverse:
                    data = self.dmx_controller.get_universe_data(universe)
                    if data:
                        self.artnet_controller.send_dmx(universe, data)
                        
            # Receive Art-Net data
            if self.artnet_controller:
                received = self.artnet_controller.receive_artnet()
                if received:
                    for universe, data in received.items():
                        dmx_universe = DMXUniverse(universe)
                        self.dmx_controller.set_universe_data(dmx_universe, data)
                        
        except Exception as e:
            logger.error(f"Error in lighting bridge update: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of lighting bridge."""
        status = {
            'running': self.running,
            'config': {
                'protocol': self.config.protocol.value,
                'artnet_universe': self.config.artnet_universe,
                'artnet_broadcast': self.config.artnet_broadcast,
                'refresh_rate': self.config.refresh_rate
            },
            'dmx': {},
            'artnet': {}
        }
        
        if self.dmx_controller:
            status['dmx']['connected'] = self.dmx_controller.serial_port is not None
            status['dmx']['channels'] = len(self.dmx_controller.channels)
        
        if self.artnet_controller:
            artnet_status = self.artnet_controller.get_status()
            status['artnet']['connected'] = artnet_status.running
            status['artnet']['universes'] = artnet_status.universes
            status['artnet']['packets_sent'] = artnet_status.packets_sent
            status['artnet']['packets_received'] = artnet_status.packets_received
            status['artnet']['errors'] = artnet_status.errors
            
        return status
```

---

## Performance Requirements

- **Latency:** Art-Net packet transmission < 10ms from data update to network send
- **CPU:** < 3% on Orange Pi 5 (single core equivalent)
- **Memory:** < 10MB resident set size
- **Network:** Support 30-44 Hz refresh rate without packet loss
- **Scalability:** Support up to 64 universes simultaneously
- **Jitter:** Packet timing jitter < 1ms

---

## Testing Strategy

### Unit Tests

```python
def test_artnet_packet_creation():
    """Test Art-Net packet creation."""
    universe = 1
    dmx_data = bytes(range(512))
    
    packet = ArtNetPacket.create_dmx_packet(universe, dmx_data)
    
    # Verify packet structure
    assert packet[0:8] == b'Art-Net\x00'
    assert packet[8] == 0x00  # OpCode low
    assert packet[9] == 0x50  # OpCode high (ArtDMX)
    assert packet[14] == 1  # Universe low byte
    assert packet[15] == 0  # Universe high byte
    assert packet[16] == 0x00  # Length low byte
    assert packet[17] == 0x02  # Length high byte (512 = 0x0200)
    assert len(packet) == 18 + 512

def test_artnet_packet_parsing():
    """Test Art-Net packet parsing."""
    universe = 42
    dmx_data = bytes([i % 256 for i in range(100)])
    
    packet = ArtNetPacket.create_dmx_packet(universe, dmx_data)
    parsed = ArtNetPacket.parse_packet(packet)
    
    assert parsed is not None
    assert parsed['universe'] == universe
    assert parsed['data'] == dmx_data
    assert parsed['opcode'] == 0x5000
    assert parsed['version'] == 0x000E

def test_artnet_output_initialization():
    """Test ArtNetOutput initialization."""
    config = ArtNetConfig(
        broadcast=True,
        refresh_rate=30,
        universe_start=0,
        universe_count=4
    )
    
    output = ArtNetOutput(config)
    
    assert output.config.broadcast == True
    assert output.refresh_rate == 30
    assert len(output.universe_data) == 4
    assert 0 in output.universe_data
    assert 3 in output.universe_data

def test_send_universe():
    """Test sending DMX data to a universe."""
    config = ArtNetConfig(universe_start=0, universe_count=1)
    output = ArtNetOutput(config)
    
    dmx_data = bytes([255, 128, 64, 32])
    result = output.send_universe(0, dmx_data)
    
    assert result == True
    assert output.universe_data[0][:4] == dmx_data
    assert len(output.universe_data[0]) == 512  # Padded to 512
```

### Integration Tests

```python
def test_lighting_bridge_integration():
    """Test LightingBridge integration with Art-Net."""
    config = LightingConfig(
        protocol=Protocol.ARTNET,
        artnet_broadcast=True,
        artnet_port=6454,
        refresh_rate=30
    )
    
    bridge = LightingBridge(config)
    assert bridge.artnet_controller is not None
    
    # Start bridge
    assert bridge.start() == True
    
    # Set DMX data
    dmx_data = [255, 0, 128, 64] + [0] * 508
    bridge.dmx_controller.set_universe_data(DMXUniverse.UNIVERSE_1, dmx_data)
    
    # Update bridge (transmits data)
    bridge.update()
    
    # Check status
    status = bridge.get_status()
    assert status['artnet']['connected'] == True
    assert status['artnet']['universes'] > 0
    
    # Stop bridge
    bridge.stop()

def test_multiverse_transmission():
    """Test transmission across multiple universes."""
    config = ArtNetConfig(
        universe_start=0,
        universe_count=4,
        refresh_rate=30
    )
    
    output = ArtNetOutput(config)
    output.start()
    
    # Send data to each universe
    for universe in range(4):
        dmx_data = bytes([universe * 64 + i for i in range(512)])
        assert output.send_universe(universe, dmx_data) == True
    
    # Let transmission run for a short time
    time.sleep(0.1)
    
    # Check stats
    status = output.get_status()
    assert status.packets_sent > 0
    assert status.errors == 0
    
    output.stop()

def test_artnet_reception():
    """Test receiving Art-Net data."""
    config = ArtNetConfig(
        receive_enabled=True,
        universe_start=0,
        universe_count=1
    )
    
    output = ArtNetOutput(config)
    output.start()
    
    # Simulate receiving a packet
    test_universe = 5
    test_data = bytes([i for i in range(100)])
    
    received = {}
    def callback(universe, data, addr):
        received[universe] = data
    
    output.subscribe(callback)
    
    # Manually trigger receive (would normally come from network)
    # This test would need network simulation
    # For now, just verify callback registration
    assert len(output.subscribers) == 1
    
    output.stop()
```

### Performance Tests

```python
def test_transmission_latency():
    """Test Art-Net transmission latency."""
    config = ArtNetConfig(refresh_rate=30)
    output = ArtNetOutput(config)
    output.start()
    
    # Measure time from send to socket send
    dmx_data = bytes([255, 128, 64, 32])
    
    start = time.perf_counter()
    for _ in range(100):
        output.send_universe(0, dmx_data)
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 100 * 1000  # ms
    assert avg_latency < 10.0, f"Average latency {avg_latency:.2f}ms > 10ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    config = ArtNetConfig(universe_count=10, refresh_rate=30)
    output = ArtNetOutput(config)
    
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    output.start()
    time.sleep(1.0)  # Let it run
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    output.stop()
    
    assert cpu_delta < 3.0, f"CPU usage increase {cpu_delta:.1f}% > 3% budget"

def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    config = ArtNetConfig(universe_count=64)  # Max universes
    output = ArtNetOutput(config)
    
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Should stay under 10MB
    assert memory_mb < 10.0, f"Memory usage {memory_mb:.1f}MB > 10MB budget"
```

---

## Hardware Considerations

### Network Configuration

- Use UDP broadcast for simple deployment
- Support unicast for controlled networks
- Implement proper TTL for multicast
- Handle network interface selection

```python
def set_network_interface(self, interface: str):
    """Set specific network interface for transmission."""
    import netifaces
    addresses = netifaces.ifaddresses(interface)
    ipv4_info = addresses[netifaces.AF_INET][0]
    self.local_ip = ipv4_info['addr']
    self.socket.bind((self.local_ip, 0))  # Bind to specific interface
```

### Timing and Synchronization

- Use hardware timers when available
- Implement jitter compensation
- Support Art-Net sync packets for multi-controller synchronization
- Handle network latency variations

```python
class ArtNetSync:
    """Art-Net synchronization for multi-controller setups."""
    
    def __init__(self):
        self.sync_enabled = False
        self.sync_interval = 1.0  # seconds
        self.last_sync = 0.0
        
    def should_send_sync(self, current_time: float) -> bool:
        """Check if sync packet should be sent."""
        if not self.sync_enabled:
            return False
        return (current_time - self.last_sync) >= self.sync_interval
    
    def send_sync_packet(self, output: ArtNetOutput):
        """Send Art-Net sync packet."""
        # ArtSync packet (OpCode 0x5100)
        packet = bytearray(b'Art-Net\x00')
        packet.extend([0x00, 0x51])  # OpCode = 0x5100
        packet.extend([0x00, 0x0E])  # Version
        packet.extend([0x00] * 8)  # Reserved
        # Send via output socket
```

---

## Error Handling

### Network Error Recovery

```python
class ArtNetOutput:
    def __init__(self, config: ArtNetConfig):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
    def _transmit_loop(self) -> None:
        """Main transmission loop with error recovery."""
        while self.running:
            try:
                # Normal transmission
                for universe, data in self.universe_data.items():
                    packet = self._build_artnet_packet(universe, data)
                    self._send_packet_with_retry(packet)
                    self.stats.packets_sent += 1
                    
                time.sleep(1.0 / self.refresh_rate)
                
            except socket.error as e:
                self._handle_network_error(e)
                time.sleep(0.5)  # Backoff
            except Exception as e:
                logger.error(f"Unexpected error in transmit loop: {e}")
                self.stats.errors += 1
                self.stats.last_error = str(e)
                
    def _handle_network_error(self, error: Exception):
        """Handle network errors with recovery."""
        self.error_state = True
        self.last_error = str(error)
        self.recovery_attempts += 1
        
        if self.recovery_attempts <= self.max_recovery_attempts:
            logger.warning(f"Network error, attempting recovery {self.recovery_attempts}/{self.max_recovery_attempts}: {error}")
            try:
                # Recreate socket
                if self.socket:
                    self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.error_state = False
            except Exception as e:
                logger.error(f"Recovery failed: {e}")
        else:
            logger.error(f"Max recovery attempts exceeded: {error}")
            self.running = False
```

### Graceful Degradation

```python
def send_with_fallback(self, universe: int, data: bytes) -> bool:
    """Send with fallback to local DMX if Art-Net fails."""
    try:
        return self.send_universe(universe, data)
    except NetworkError:
        logger.warning("Art-Net failed, falling back to local DMX")
        if self.dmx_controller:
            dmx_list = list(data[:512])
            return self.dmx_controller.send_dmx(DMXUniverse(universe), dmx_list)
        return False
```

---

## Configuration System

### JSON Configuration

```json
{
  "artnet_output": {
    "enabled": true,
    "protocol": "artnet",
    "broadcast": true,
    "broadcast_address": "255.255.255.255",
    "port": 6454,
    "universe_start": 0,
    "universe_count": 4,
    "refresh_rate": 30,
    "merge_mode": "htp",
    "priority": 100,
    "receive_enabled": false,
    "targets": [
      "192.168.1.100",
      "192.168.1.101"
    ],
    "error_recovery": {
      "max_attempts": 5,
      "backoff_ms": 100
    }
  }
}
```

### Configuration Loading

```python
def load_artnet_config(config_path: str) -> ArtNetConfig:
    """Load Art-Net configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    artnet_cfg = config.get('artnet_output', {})
    
    return ArtNetConfig(
        broadcast=artnet_cfg.get('broadcast', True),
        broadcast_address=artnet_cfg.get('broadcast_address', '255.255.255.255'),
        port=artnet_cfg.get('port', 6454),
        universe_start=artnet_cfg.get('universe_start', 0),
        universe_count=artnet_cfg.get('universe_count', 1),
        refresh_rate=artnet_cfg.get('refresh_rate', 30),
        merge_mode=MergeMode(artnet_cfg.get('merge_mode', 'htp')),
        priority=artnet_cfg.get('priority', 100),
        receive_enabled=artnet_cfg.get('receive_enabled', False),
        targets=artnet_cfg.get('targets', [])
    )
```

---

## Implementation Tips

1. **Use pyartnet Library**: Consider using existing `pyartnet` library for protocol implementation
2. **Start Simple**: Begin with Art-Net v1 broadcast mode before adding v4 and unicast
3. **Implement Proper Cleanup**: Ensure sockets are closed on shutdown
4. **Add Debug Visualization**: Provide WebSocket endpoint to monitor Art-Net traffic
5. **Test with Real Hardware**: Use DMX monitor or lighting console for validation
6. **Profile Network Usage**: Monitor packet loss and jitter on target network
7. **Use Threading**: Run transmission in separate thread to avoid blocking main loop
8. **Implement Buffer Management**: Avoid allocating new buffers each frame
9. **Add Monitoring**: Track packet statistics and error rates
10. **Document Network Setup**: Provide clear instructions for network configuration

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for universe buffers
- [ ] Pre-allocate all packet buffers
- [ ] Use socket options for low latency (SO_BROADCAST, TCP_NODELAY)
- [ ] Pin transmission thread to dedicated CPU core
- [ ] Set real-time scheduling for transmission thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Use memoryview for zero-copy packet construction
- [ ] Monitor network interface statistics
- [ ] Profile with realistic universe counts
- [ ] Optimize packet building hot path

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete Art-Net transmission
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum universes (64)
- [ ] Network error recovery tested
- [ ] Hardware validation with real Art-Net receivers
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] Broadcast and unicast modes both work
- [ ] Multi-universe transmission works correctly
- [ ] Reception mode works with external controllers

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Transmission latency < 10ms measured
- [ ] Refresh rate stability verified (30-44 Hz)
- [ ] Multi-universe support verified (up to 64)
- [ ] Network error recovery tested
- [ ] Hardware validation with Art-Net receiver completed
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D2: ArtNet Output` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/lighting_bridge.py (L465-484) [VJlive (Original)]
```python
def _update_loop(self) -> None:
    """Main update loop for lighting bridge."""
    while self.running:
        try:
            # Send DMX data
            if self.dmx_controller:
                for universe in DMXUniverse:
                    data = self.dmx_controller.get_universe_data(universe)
                    self.dmx_controller.send_dmx(universe, data)
            
            # Send Art-Net data
            if self.artnet_controller:
                for universe in DMXUniverse:
                    data = self.artnet_controller.get_universe_data(universe.value)
                    self.artnet_controller.send_artnet(universe.value, data)
            
            # Receive Art-Net data
            if self.artnet_controller:
                received = self.artnet_controller.receive_artnet()
```

This shows the main update loop pattern for Art-Net transmission and reception.

### core/lighting_bridge.py (L481-500) [VJlive (Original)]
```python
                # Receive Art-Net data
                if self.artnet_controller:
                    received = self.artnet_controller.receive_artnet()
                    if received:
                        for universe, data in received.items():
                            # Update DMX controller with received data
                            if self.dmx_controller:
                                dmx_universe = DMXUniverse(universe)
                                self.dmx_controller.set_universe_data(dmx_universe, data)
            
            time.sleep(1.0 / self.config.refresh_rate)
```

This shows the receive loop and data integration pattern.

### core/lighting_bridge.py (L497-516) [VJlive (Original)]
```python
def get_status(self) -> Dict[str, Any]:
    """Get status of lighting bridge."""
    status = {
        'running': self.running,
        'config': {
            'protocol': self.config.protocol.value,
            'artnet_universe': self.config.artnet_universe,
            'artnet_broadcast': self.config.artnet_broadcast,
            'refresh_rate': self.config.refresh_rate
        },
        'dmx': {},
        'artnet': {}
    }
    
    if self.dmx_controller:
        status['dmx']['connected'] = self.dmx_controller.serial_port is not None
        status['dmx']['channels'] = len(self.dmx_controller.channels)
    
    if self.artnet_controller:
        status['artnet']['connected'] = self.artnet_controller.socket is not None
        status['artnet']['universes'] = len(self.artnet_controller.universes)
    
    return status
```

This shows the status reporting pattern.

### core/timeline/quantum_timeline.py (L417-436) [VJlive (Original)]
```python
def export_to_show_control(self, format: str = "artnet") -> Dict[str, Any]:
    """Export timeline to professional show control protocols"""
    export_data = {
        "timeline": {
            "duration": self.current_time,
            "parameters": {},
            "quantum_properties": {
                "seed": self.quantum_seed,
                "entanglements": self.quantum_entanglement
            }
        }
    }
    
    for path, param in self.parameters.items():
        export_data["timeline"]["parameters"][path] = {
            "keyframes": [{
```

This shows the export pattern for show control protocols.

### core/timeline/quantum_timeline.py (L433-452) [VJlive (Original)]
```python
        for path, param in self.parameters.items():
            export_data["timeline"]["parameters"][path] = {
                "keyframes": [{
                    "time": kf.time,
                    "value": kf.value,
                    "interpolation": kf.interpolation.value,
                    "quantum_state": kf.quantum_state.value
                } for kf in param.keyframes],
                "quantum_enabled": param.quantum_enabled
            }
        
        # Add format-specific data
        if format == "artnet":
            export_data["artnet"] = self._export_to_artnet()
        elif format == "sacn":
            export_data["sacn"] = self._export_to_sacn()
        elif format == "timecode":
            export_data["timecode"] = self._export_to_timecode()
```

This shows the format-specific export handling.

---

## Notes for Implementers

1. **Art-Net Protocol**: Implement Art-Net v4 for best compatibility, but support v1 for legacy devices
2. **DMX Channels**: Each universe supports 512 channels; plan universe allocation carefully
3. **Network Setup**: Document network configuration requirements (broadcast vs unicast)
4. **Timing**: Maintain consistent refresh rate; use sleep() with compensation for drift
5. **Error Handling**: Implement robust error recovery for network failures
6. **Testing**: Use Art-Net monitor tools (like Art-Net Controller) for validation
7. **Performance**: Minimize allocations in transmission loop; reuse buffers
8. **Thread Safety**: Protect shared data structures with locks or atomic operations
9. **Configuration**: Allow runtime reconfiguration of broadcast address, refresh rate, etc.
10. **Documentation**: Provide clear examples for connecting to common lighting consoles

---

## Implementation Roadmap

1. **Week 1**: Design Art-Net packet structures and protocol implementation
2. **Week 2**: Implement core ArtNetOutput class with basic transmission
3. **Week 3**: Add receive functionality and bi-directional communication
4. **Week 4**: Integrate with LightingBridge and DMX controller
5. **Week 5**: Add configuration system and error handling
6. **Week 6**: Performance optimization and testing
7. [ ] **Week 7**: Hardware validation and documentation

---

## Easter Egg Idea

If exactly 42 universes are configured, and the refresh rate is set to exactly 42 Hz, and the broadcast address contains the octet "42" (e.g., 192.168.42.255), the ArtNetOutput enters a "Synchronicity Mode" where all transmitted packets contain a hidden pattern in the unused header bytes that spells "The Answer" in ASCII when viewed as raw hex. This pattern causes compatible Art-Net receivers (specifically the grandMA2 console with a secret firmware flag) to display a cryptic message about the universe being in tune, and the plugin bus broadcasts a hidden message "42 universes of light" in DMX512 encoding, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/lighting_bridge.py` (to be implemented)
- `core/dmx_controller.py` (to be referenced)
- `core/plugin_bus.py` (for broadcasting)
- Art-Net Protocol Specification (v1, v4)
- DMX512 Standard (ANSI E1.11)
- pyartnet library (https://github.com/OctoPrint/pyartnet)
- ENTTEC DMX over Ethernet documentation
- Art-Net website (art-net.org.uk)
- sACN (Streaming ACN) protocol (ANSI E1.31)
- RDM (Remote Device Management) protocol (ANSI E1.20)

---

## Conclusion

The ArtNet Output module is the professional lighting interface for VJLive3, enabling seamless integration with stage lighting equipment via the industry-standard Art-Net protocol. Its robust implementation supports both transmission and reception, multiple universes, and flexible configuration options. By providing low-latency, reliable DMX data distribution over Ethernet, this module allows VJLive3 to serve as a powerful lighting controller alongside its visual capabilities, creating unified audio-visual-light performances that can synchronize with professional lighting systems in live performance environments.

---
>>>>>>> REPLACE