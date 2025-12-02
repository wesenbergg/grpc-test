#!/usr/bin/env python3
"""
gRPC Server - Responds to Ping with Pong
Leader-only architecture: Only Raft leader accepts client requests
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
        # Log on followers when state is replicated
        if not self._isLeader():
            print(f"[FOLLOWER] Replicated state update - Counter now: {self.__counter}")
    
    def get_count(self):
        """Get current counter value."""
        return self.__counter


class PingPongServicer(pingpong_pb2_grpc.PingPongServicer):
    """Implementation of the PingPong service."""
    
    def __init__(self, counter, node_address_map):
        self.counter = counter
        self.node_address_map = node_address_map  # Map of raft_address -> grpc_address
    
    def Ping(self, request, context):
        """Responds to a ping request with a pong."""
        # Check if this node is the leader
        if not self.counter._isLeader():
            # Forward to leader
            leader = self.counter._getLeader()
            if leader is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("No leader elected yet. Please retry.")
                return pingpong_pb2.PongResponse(message="No leader available")
            
            # Get leader's gRPC address
            leader_addr = str(leader.address) if hasattr(leader, 'address') else str(leader)
            leader_grpc = self.node_address_map.get(leader_addr)
            
            if not leader_grpc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Leader address mapping not found: {leader_addr}")
                return pingpong_pb2.PongResponse(message="Leader address unknown")
            
            print(f"[FOLLOWER] Forwarding request to leader at {leader_grpc}")
            
            # Forward request to leader
            try:
                with grpc.insecure_channel(leader_grpc) as channel:
                    stub = pingpong_pb2_grpc.PingPongStub(channel)
                    response = stub.Ping(request)
                    print(f"[FOLLOWER] Received response from leader: {response.message}")
                    return response
            except Exception as e:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(f"Failed to forward to leader: {str(e)}")
                return pingpong_pb2.PongResponse(message=f"Forward failed: {str(e)}")
        
        # This node is the leader - process the request
        self.counter._increment()
        time.sleep(0.01)  # Allow replication to complete
        count = self.counter.get_count()
        
        print(f"[LEADER] Received: {request.message} (Count: {count})")
        response_message = f"Pong! (received: '{request.message}', count: {count})"
        print(f"[LEADER] Sending: {response_message}")
        return pingpong_pb2.PongResponse(message=response_message)


def serve(raft_port=4321, grpc_port=50051, partner_addresses=None, node_map=None):
    """Start the gRPC server with replicated state."""
    # Initialize Raft-based counter
    self_address = f'localhost:{raft_port}'
    partners = partner_addresses if partner_addresses else []
    
    print(f"Initializing Raft node at {self_address}")
    print(f"gRPC port: {grpc_port}")
    if partners:
        print(f"Partner nodes: {partners}")
    else:
        print("Running as single node (no replication)")
    
    counter = PingCounter(self_address, partners)
    
    # Wait a bit for Raft to initialize and elect leader
    print("Waiting for leader election...")
    time.sleep(2)
    
    # Check leadership status
    if counter._isLeader():
        print(f"✓ This node is the LEADER")
    else:
        leader = counter._getLeader()
        leader_addr = str(leader.address) if leader and hasattr(leader, 'address') else str(leader) if leader else "unknown"
        print(f"✗ This node is a FOLLOWER (Leader: {leader_addr})")
    
    # Start gRPC server (all nodes listen, but followers forward to leader)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pingpong_pb2_grpc.add_PingPongServicer_to_server(
        PingPongServicer(counter, node_map or {}), 
        server
    )
    
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    
    print(f"gRPC Server started on port {grpc_port}")
    print("Waiting for ping requests...")
    print(f"Current ping count: {counter.get_count()}")
    print("-" * 50)
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print(f"\nShutting down server... (Final count: {counter.get_count()})")
        server.stop(0)


if __name__ == "__main__":
    import sys
    
    # Usage: python server.py [grpc_port] [raft_port] [partner1_raft:partner1_grpc] [partner2_raft:partner2_grpc] ...
    # Example for 3-node cluster:
    # Node 1: python server.py 50051 4321 localhost:4322:50052 localhost:4323:50053
    # Node 2: python server.py 50052 4322 localhost:4321:50051 localhost:4323:50053
    # Node 3: python server.py 50053 4323 localhost:4321:50051 localhost:4322:50052
    
    if len(sys.argv) < 3:
        print("Usage: python server.py <grpc_port> <raft_port> [partner1_raft:partner1_grpc] ...")
        print("\nExample:")
        print("  Node 1: python server.py 50051 4321 localhost:4322:50052 localhost:4323:50053")
        print("  Node 2: python server.py 50052 4322 localhost:4321:50051 localhost:4323:50053")
        print("  Node 3: python server.py 50053 4323 localhost:4321:50051 localhost:4322:50052")
        sys.exit(1)
    
    grpc_port = int(sys.argv[1])
    raft_port = int(sys.argv[2])
    
    # Parse partner addresses and build mapping
    partners = []
    node_map = {}
    
    for arg in sys.argv[3:]:
        if ':' in arg:
            parts = arg.split(':')
            if len(parts) == 3:  # host:raft_port:grpc_port
                host, r_port, g_port = parts
                raft_addr = f"{host}:{r_port}"
                grpc_addr = f"{host}:{g_port}"
                partners.append(raft_addr)
                node_map[raft_addr] = grpc_addr
            else:  # Just raft address
                partners.append(arg)
    
    # Add self to map
    node_map[f"localhost:{raft_port}"] = f"localhost:{grpc_port}"
    
    print("Node address mapping:")
    for raft_addr, grpc_addr in node_map.items():
        print(f"  Raft {raft_addr} -> gRPC {grpc_addr}")
    print()
    
    serve(raft_port, grpc_port, partners, node_map)
