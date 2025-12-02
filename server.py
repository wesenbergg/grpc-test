#!/usr/bin/env python3
"""
gRPC Server - Responds to Ping with Pong
"""
import grpc
from concurrent import futures
import time
from pysyncobj import SyncObj, replicated

import pingpong_pb2
import pingpong_pb2_grpc


class PingCounter(SyncObj):
    """Replicated counter using Raft consensus."""
    
    def __init__(self, selfAddress, partnerAddrs):
        super(PingCounter, self).__init__(selfAddress, partnerAddrs)
        self.__counter = 0
    
    @replicated
    def _increment(self):
        """Increment the counter (replicated operation)."""
        self.__counter += 1
        return self.__counter
    
    def get_count(self):
        """Get current counter value."""
        return self.__counter


class PingPongServicer(pingpong_pb2_grpc.PingPongServicer):
    """Implementation of the PingPong service."""
    
    def __init__(self, counter):
        self.counter = counter
    
    def Ping(self, request, context):
        """Responds to a ping request with a pong."""
        # Increment the replicated counter
        self.counter._increment()
        count = self.counter.get_count()
        print(f"Received: {request.message} (Count: {count})")
        response_message = f"Pong! (received: '{request.message}', count: {count})"
        print(f"Sending: {response_message}")
        return pingpong_pb2.PongResponse(message=response_message)


def serve(raft_port=4321, partner_addresses=None):
    """Start the gRPC server with replicated state."""
    # Initialize Raft-based counter
    self_address = f'localhost:{raft_port}'
    partners = partner_addresses if partner_addresses else []
    
    print(f"Initializing Raft node at {self_address}")
    if partners:
        print(f"Partner nodes: {partners}")
    else:
        print("Running as single node (no replication)")
    
    counter = PingCounter(self_address, partners)
    
    # Wait a bit for Raft to initialize
    time.sleep(1)
    
    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pingpong_pb2_grpc.add_PingPongServicer_to_server(PingPongServicer(counter), server)
    
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    
    print(f"gRPC Server started on port {port}")
    print("Waiting for ping requests...")
    print(f"Current ping count: {counter.get_count()}")
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print(f"\nShutting down server... (Final count: {counter.get_count()})")
        server.stop(0)


if __name__ == "__main__":
    import sys
    
    # Allow specifying Raft port and partner nodes via command line
    # Usage: python server.py [raft_port] [partner1:port] [partner2:port] ...
    # Example: python server.py 4321 localhost:4322 localhost:4323
    
    raft_port = int(sys.argv[1]) if len(sys.argv) > 1 else 4321
    partners = sys.argv[2:] if len(sys.argv) > 2 else []
    
    serve(raft_port, partners)
