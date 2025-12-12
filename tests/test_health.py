"""
Unit tests for health routes
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import grpc

from server.routes.health import health_bp
from flask import Flask


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


class TestHealthEndpoint:
    """Test /health endpoint"""
    
    def test_health_check_success(self, client):
        """Should return ok when gRPC is connected"""
        with patch('server.routes.health.ping_stub') as mock_stub:
            mock_stub.Ping.return_value = Mock()
            
            response = client.get('/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['grpc_connected'] is True
    
    def test_health_check_failure(self, client):
        """Should return degraded when gRPC fails"""
        with patch('server.routes.health.ping_stub') as mock_stub:
            mock_stub.Ping.side_effect = Exception("Connection failed")
            
            response = client.get('/health')
            
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'degraded'
            assert data['grpc_connected'] is False


class TestPingEndpoint:
    """Test /ping endpoint"""
    
    def test_ping_success(self, client):
        """Should return pong response when gRPC works"""
        with patch('server.routes.health.ping_stub') as mock_stub:
            mock_response = Mock()
            mock_response.message = "Pong! (received: 'Ping!', count: 1)"
            mock_stub.Ping.return_value = mock_response
            
            response = client.get('/ping')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'Pong' in data['response']
    
    def test_ping_grpc_error(self, client):
        """Should handle gRPC errors gracefully"""
        with patch('server.routes.health.ping_stub') as mock_stub:
            mock_error = grpc.RpcError()
            mock_error.code = lambda: grpc.StatusCode.UNAVAILABLE
            mock_error.details = lambda: "Service unavailable"
            mock_stub.Ping.side_effect = mock_error
            
            response = client.get('/ping')
            
            assert response.status_code == 503
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data
    
    def test_ping_general_exception(self, client):
        """Should handle general exceptions gracefully"""
        with patch('server.routes.health.ping_stub') as mock_stub:
            mock_stub.Ping.side_effect = Exception("Unexpected error")
            
            response = client.get('/ping')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data