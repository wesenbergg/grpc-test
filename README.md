# gRPC Ping-Pong Example

A simple example of two Python programs communicating via gRPC.

<img width="1704" height="1037" alt="image" src="https://github.com/user-attachments/assets/95f0b9de-8e82-43f6-862a-60001859a120" />


## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Generate gRPC code from the proto file:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. pingpong.proto
```

## Running

1. Start the server in one terminal:

```bash
python server.py
```

2. In another terminal, run the client:

```bash
python client.py
```

The client will send a "Ping!" message to the server, and the server will respond with "Pong!".

## Files

- `pingpong.proto` - Protocol Buffer definition for the ping-pong service
- `server.py` - gRPC server that responds to ping requests
- `client.py` - gRPC client that sends ping requests
- `requirements.txt` - Python dependencies
