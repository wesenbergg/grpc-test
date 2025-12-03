#!/usr/bin/env python3
"""
gRPC Server - Responds to Ping with Pong
Leader-only architecture: Only Raft leader accepts client requests
"""
import grpc
from concurrent import futures
import time

from raft.pingServicer import PingPongServicer
from raft.state import GlobalState
from rpc import pingpong_pb2_grpc


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
    
    globalState = GlobalState(self_address, partners)
    
    # Wait a bit for Raft to initialize and elect leader
    print("Waiting for leader election...")
    time.sleep(2)
    
    # Check leadership status
    if globalState._isLeader():
        print(f"✓ This node is the LEADER")
    else:
        leader = globalState._getLeader()
        leader_addr = str(leader.address) if leader and hasattr(leader, 'address') else str(leader) if leader else "unknown"
        print(f"✗ This node is a FOLLOWER (Leader: {leader_addr})")
    
    # Start gRPC server (all nodes listen, but followers forward to leader)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pingpong_pb2_grpc.add_PingPongServicer_to_server(
        PingPongServicer(globalState, node_map or {}), 
        server
    )
    
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    
    print(f"gRPC Server started on port {grpc_port}")
    print("Waiting for ping requests...")
    print(f"Current ping count: {globalState.get_count()}")
    print("-" * 50)
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print(f"\nShutting down server... (Final count: {globalState.get_count()})")
        server.stop(0)

