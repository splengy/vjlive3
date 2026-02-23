import pytest
import threading

def test_signal_bus_singleton():
    """Verify SignalBus is a singleton across imports."""
    bus1 = SignalBus()
    bus2 = SignalBus()
    assert id(bus1) == id(bus2)
    assert id(bus1) == id(bus)

def test_signal_bus_rw():
    """Verify basic read/write operations without threading."""
    bus.clear()
    assert bus.read("test.channel") == 0.0  # Default fallback
    assert bus.read("test.channel", default=0.5) == 0.5
    
    bus.write("test.channel", 0.75)
    assert bus.read("test.channel") == 0.75
    
    # Update value
    bus.write("test.channel", 1.0)
    assert bus.read("test.channel") == 1.0

def test_signal_bus_get_all():
    """Verify get_all returns a snapshot dict."""
    bus.clear()
    bus.write("ch.1", 0.1)
    bus.write("ch.2", 0.2)
    
    snapshot = bus.get_all()
    assert len(snapshot) == 2
    assert snapshot["ch.1"] == 0.1
    assert snapshot["ch.2"] == 0.2
    
def test_signal_bus_threading():
    """Verify bus can handle concurrent writes from multiple threads safely."""
    bus.clear()
    threads = []
    
    def worker(idx):
        for i in range(100):
            bus.write(f"thread.{idx}", float(i) / 100.0)
            
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    snapshot = bus.get_all()
    assert len(snapshot) == 10
    for i in range(10):
        assert snapshot[f"thread.{i}"] == 0.99
    
    bus.clear()
