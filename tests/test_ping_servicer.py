"""
Unit tests for PingPongServicer
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import grpc

from raft.pingServicer import PingPongServicer
from rpc import pingpong_pb2


class TestPingPongServicerAsLeader:
    """Test PingPong servicer when node is leader"""
    
    def test_ping_as_leader(self, mock_grpc_context):
        """Leader should process ping request directly"""
        # Setup mock counter
        mock_counter = Mock()
        mock_counter._isLeader.return_value = True
        mock_counter.get_count.return_value = 5
        
        servicer = PingPongServicer(mock_counter, {})
        request = pingpong_pb2.PingRequest(message="Test Ping")
        
        response = servicer.Ping(request, mock_grpc_context)
        
        assert "Pong!" in response.message
        assert "Test Ping" in response.message
        assert "5" in response.message
        mock_counter._increment.assert_called_once()
    
    def test_counter_increments_on_ping(self, mock_grpc_context):
        """Counter should increment when leader receives ping"""
        mock_counter = Mock()
        mock_counter._isLeader.return_value = True
        mock_counter.get_count.return_value = 1
        
        servicer = PingPongServicer(mock_counter, {})
        request = pingpong_pb2.PingRequest(message="Ping")
        
        servicer.Ping(request, mock_grpc_context)
        
        mock_counter._increment.assert_called_once()


class TestPingPongServicerAsFollower:
    """Test PingPong servicer when node is follower"""
    
    def test_forward_to_leader(self, mock_grpc_context):
        """Follower should forward request to leader"""
        # Setup mock counter as follower
        mock_counter = Mock()
        mock_counter._isLeader.return_value = False
        mock_leader = Mock()
        mock_leader.address = 'localhost:4321'
        mock_counter._getLeader.return_value = mock_leader
        
        node_address_map = {'localhost:4321': 'localhost:50051'}
        
        # Mock the gRPC channel and stub
        with patch('raft.pingServicer.grpc.insecure_channel') as mock_channel:
            mock_stub = MagicMock()
            mock_stub.Ping.return_value = pingpong_pb2.PongResponse(message="Forwarded Pong!")
            mock_channel.return_value.__enter__.return_value = MagicMock()
            
            with patch('raft.pingServicer.pingpong_pb2_grpc.PingPongStub', return_value=mock_stub):
                servicer = PingPongServicer(mock_counter, node_address_map)
                request = pingpong_pb2.PingRequest(message="Ping")
                
                response = servicer.Ping(request, mock_grpc_context)
                
                assert response.message == "Forwarded Pong!"
                mock_stub.Ping.assert_called_once()
    
    def test_no_leader_elected(self, mock_grpc_context):
        """Should return error when no leader is elected"""
        mock_counter = Mock()
        mock_counter._isLeader.return_value = False
        mock_counter._getLeader.return_value = None
        
        servicer = PingPongServicer(mock_counter, {})
        request = pingpong_pb2.PingRequest(message="Ping")
        
        response = servicer.Ping(request, mock_grpc_context)
        
        assert "No leader" in response.message
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.UNAVAILABLE)
    
    def test_leader_address_not_found(self, mock_grpc_context):
        """Should return error when leader address mapping is missing"""
        mock_counter = Mock()
        mock_counter._isLeader.return_value = False
        mock_leader = Mock()
        mock_leader.address = 'localhost:4321'
        mock_counter._getLeader.return_value = mock_leader
        
        # Empty address map
        servicer = PingPongServicer(mock_counter, {})
        request = pingpong_pb2.PingRequest(message="Ping")
        
        response = servicer.Ping(request, mock_grpc_context)
        
        assert "address unknown" in response.message.lower()
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)
    
    def test_forward_fails(self, mock_grpc_context):
        """Should handle forward failure gracefully"""
        mock_counter = Mock()
        mock_counter._isLeader.return_value = False
        mock_leader = Mock()
        mock_leader.address = 'localhost:4321'
        mock_counter._getLeader.return_value = mock_leader
        
        node_address_map = {'localhost:4321': 'localhost:50051'}
        
        with patch('raft.pingServicer.grpc.insecure_channel') as mock_channel:
            mock_channel.side_effect = Exception("Connection failed")
            
            servicer = PingPongServicer(mock_counter, node_address_map)
            request = pingpong_pb2.PingRequest(message="Ping")
            
            response = servicer.Ping(request, mock_grpc_context)
            
            assert "failed" in response.message.lower()
            mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.UNAVAILABLE)