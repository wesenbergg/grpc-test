"""
Unit tests for CLI client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import grpc

from cli.client import run
from rpc import pingpong_pb2


class TestClientRun:
    """Test client gRPC call"""
    
    def test_successful_ping(self):
        """Should successfully send ping and receive pong"""
        with patch('cli.client.grpc.insecure_channel') as mock_channel:
            # Setup mock
            mock_stub = Mock()
            mock_response = pingpong_pb2.PongResponse(message="Pong! (received: 'Ping!', count: 1)")
            mock_stub.Ping.return_value = mock_response
            
            mock_channel_instance = MagicMock()
            mock_channel.return_value.__enter__.return_value = mock_channel_instance
            
            with patch('cli.client.pingpong_pb2_grpc.PingPongStub', return_value=mock_stub):
                # Should not raise exception
                run()
                
                # Verify stub was called
                mock_stub.Ping.assert_called_once()
    
    def test_grpc_error_handling(self):
        """Should handle gRPC errors gracefully"""
        with patch('cli.client.grpc.insecure_channel') as mock_channel:
            mock_stub = Mock()
            mock_error = grpc.RpcError()
            mock_error.code = lambda: grpc.StatusCode.UNAVAILABLE
            mock_error.details = lambda: "Service unavailable"
            mock_stub.Ping.side_effect = mock_error
            
            mock_channel_instance = MagicMock()
            mock_channel.return_value.__enter__.return_value = mock_channel_instance
            
            with patch('cli.client.pingpong_pb2_grpc.PingPongStub', return_value=mock_stub):
                # Should not crash
                run()
    
    def test_client_creates_correct_request(self):
        """Should create correct ping request"""
        with patch('cli.client.grpc.insecure_channel') as mock_channel:
            mock_stub = Mock()
            mock_response = pingpong_pb2.PongResponse(message="Pong!")
            mock_stub.Ping.return_value = mock_response
            
            mock_channel_instance = MagicMock()
            mock_channel.return_value.__enter__.return_value = mock_channel_instance
            
            with patch('cli.client.pingpong_pb2_grpc.PingPongStub', return_value=mock_stub):
                run()
                
                # Check that Ping was called with correct message
                call_args = mock_stub.Ping.call_args
                assert call_args is not None
                request = call_args[0][0]
                assert request.message == "Ping!"