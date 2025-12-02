#!/usr/bin/env python3
"""
REST Gateway - Translates HTTP requests to gRPC
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import grpc

import pingpong_pb2
import pingpong_pb2_grpc

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# gRPC client connection
channel = grpc.insecure_channel('localhost:50051')
stub = pingpong_pb2_grpc.PingPongStub(channel)


@app.route('/ping', methods=['GET'])
def ping():
    """REST endpoint that calls gRPC service"""
    try:        
        # Call gRPC service
        grpc_request = pingpong_pb2.PingRequest(message='Ping!')
        grpc_response = stub.Ping(grpc_request)
        
        return jsonify({
            'success': True,
            'response': grpc_response.message
        })
    except grpc.RpcError as e:
        return jsonify({
            'success': False,
            'error': f'{e.code()}: {e.details()}'
        }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Try to call the gRPC service
        grpc_request = pingpong_pb2.PingRequest(message='health check')
        stub.Ping(grpc_request)
        return jsonify({
            'status': 'ok',
            'grpc_connected': True
        })
    except:
        return jsonify({
            'status': 'degraded',
            'grpc_connected': False
        }), 503


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'PingPong REST Gateway',
        'version': '1.0',
        'endpoints': {
            'POST /ping': {
                'description': 'Send a ping message',
                'body': {'message': 'string'},
                'example': {'message': 'Hello from frontend!'}
            },
            'GET /health': {
                'description': 'Check service health'
            }
        }
    })


if __name__ == '__main__':
    print("=" * 50)
    print("REST Gateway running on http://localhost:5000")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST http://localhost:5000/ping")
    print("  GET  http://localhost:5000/health")
    print("\nExample curl command:")
    print("  curl -X POST http://localhost:5000/ping \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"message\": \"Hello from REST!\"}'")
    print("\n" + "=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')
