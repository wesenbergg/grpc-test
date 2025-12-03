#!/usr/bin/env python3
"""
gRPC Client - Sends Ping and receives Pong
"""
import grpc

import sys
from pathlib import Path
# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Now you can import from rpc folder
from rpc import pingpong_pb2
from rpc import pingpong_pb2_grpc


def run():
    """Send a ping request to the server."""
    # Create a channel to connect to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = pingpong_pb2_grpc.PingPongStub(channel)
        
        # Create a ping request
        ping_message = "Ping!"
        print(f"Sending: {ping_message}")
        
        # Make the RPC call
        try:
            response = stub.Ping(pingpong_pb2.PingRequest(message=ping_message))
            print(f"Received: {response.message}")
        except grpc.RpcError as e:
            print(f"Error: {e.code()}: {e.details()}")


if __name__ == "__main__":
    run()
