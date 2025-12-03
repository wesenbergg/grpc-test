"""Entry point when running raft as a module: python -m raft"""
import sys
from raft.server import serve

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python server.py <grpc_port> <raft_port> [partner1_raft:partner1_grpc] ...\n\nExample:\n  Node 1: python server.py 50051 4321 localhost:4322:50052 localhost:4323:50053\n  Node 2: python server.py 50052 4322 localhost:4321:50051 localhost:4323:50053\n  Node 3: python server.py 50053 4323 localhost:4321:50051 localhost:4322:50052")
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
