import time
import pytest
import zmq
from vjlive3.sync.zmq_coordinator import ZmqCoordinator, ZmqMessage

def test_pub_sub_local():
    # Setup Coordinator A (Publisher)
    coord_pub = ZmqCoordinator("NodePub")
    coord_pub.bind_publisher(5555)

    # Setup Coordinator B (Subscriber)
    coord_sub = ZmqCoordinator("NodeSub")
    coord_sub.connect_subscriber("tcp://127.0.0.1:5555", ["beat."])

    received_msgs = []
    def callback(msg: ZmqMessage):
        received_msgs.append(msg)

    coord_sub.subscribe("beat.kick", callback)

    # Give ZMQ time to handshake
    time.sleep(0.1)

    # Publish message
    coord_pub.publish("beat.kick", {"velocity": 127})

    # Poll and receive
    time.sleep(0.05)
    coord_sub.poll_events(100)

    assert len(received_msgs) == 1
    assert received_msgs[0].topic == "beat.kick"
    assert received_msgs[0].payload == {"velocity": 127}
    assert isinstance(received_msgs[0].timestamp, float)

    coord_pub.shutdown()
    coord_sub.shutdown()


def test_topic_filtering():
    coord_pub = ZmqCoordinator("NodePub2")
    coord_pub.bind_publisher(5556)

    coord_sub = ZmqCoordinator("NodeSub2")
    # Subscribing to "state." only
    coord_sub.connect_subscriber("tcp://127.0.0.1:5556", ["state."])

    messages_received = []
    
    # We will subscribe internally to "state." but also add a callback for "beat."
    # to prove the socket layer filters it before our callbacks ever see it.
    coord_sub.subscribe("state.update", lambda msg: messages_received.append(msg))
    coord_sub.subscribe("beat.kick", lambda msg: messages_received.append(msg))

    time.sleep(0.1)

    # Publish both topics
    coord_pub.publish("state.update", {"fps": 60})
    coord_pub.publish("beat.kick", {"velocity": 100})

    time.sleep(0.05)
    coord_sub.poll_events(100)

    assert len(messages_received) == 1
    assert messages_received[0].topic == "state.update"
    
    coord_pub.shutdown()
    coord_sub.shutdown()


def test_json_serialization_error():
    coord = ZmqCoordinator("PublisherOnly")
    coord.bind_publisher(5557)
    
    class NonSerializable:
        pass
        
    with pytest.raises(ValueError, match="Payload not JSON serializable"):
        coord.publish("state.error", {"obj": NonSerializable()})
        
    coord.shutdown()


def test_clean_shutdown():
    coord = ZmqCoordinator("ShutdownTest")
    coord.bind_publisher(5558)
    coord.connect_subscriber("tcp://127.0.0.1:5558", ["all"])
    
    assert coord.pub_socket is not None
    assert len(coord.sub_sockets) == 1
    
    coord.shutdown()
    
    assert coord.pub_socket is None
    assert len(coord.sub_sockets) == 0
