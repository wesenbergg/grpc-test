"""
Unit tests for showtime routes
"""
import pytest
from unittest.mock import Mock, patch
import grpc
import json

from server.routes.showtime import showtime_bp
from flask import Flask
from rpc import showtimes_pb2


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(showtime_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


class TestGetShowtimes:
    """Test GET /showtimes endpoint"""
    
    def test_get_all_showtimes_success(self, client):
        """Should return all showtimes"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            # Create mock response
            mock_response = Mock()
            mock_showtime1 = Mock()
            mock_showtime1.movie_id = 1
            mock_showtime1.theater_id = 1
            mock_showtime1.time = '2024-07-01T19:00:00'
            mock_showtime1.price = 12.50
            mock_showtime1.reserved_seats = {'A1': Mock(user='Alice')}
            
            mock_response.showtimes = {'1': mock_showtime1}
            mock_stub.GetShowtimes.return_value = mock_response
            
            response = client.get('/showtimes')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert '1' in data['showtimes']
    
    def test_get_showtimes_grpc_error(self, client):
        """Should handle gRPC errors"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_error = grpc.RpcError()
            mock_error.code = lambda: grpc.StatusCode.UNAVAILABLE
            mock_error.details = lambda: "Service unavailable"
            mock_stub.GetShowtimes.side_effect = mock_error
            
            response = client.get('/showtimes')
            
            assert response.status_code == 503
            data = response.get_json()
            assert data['success'] is False


class TestGetShowtime:
    """Test GET /showtimes/<id> endpoint"""
    
    def test_get_showtime_found(self, client):
        """Should return specific showtime"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_response = Mock()
            mock_response.found = True
            mock_showtime = Mock()
            mock_showtime.movie_id = 1
            mock_showtime.theater_id = 1
            mock_showtime.time = '2024-07-01T19:00:00'
            mock_showtime.price = 12.50
            mock_showtime.reserved_seats = {}
            mock_response.showtime = mock_showtime
            mock_stub.GetShowtime.return_value = mock_response
            
            response = client.get('/showtimes/1')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['showtime']['movie_id'] == 1
    
    def test_get_showtime_not_found(self, client):
        """Should return 404 for nonexistent showtime"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_response = Mock()
            mock_response.found = False
            mock_stub.GetShowtime.return_value = mock_response
            
            response = client.get('/showtimes/999')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False


class TestAddShowtime:
    """Test POST /showtimes endpoint"""
    
    def test_add_showtime_success(self, client):
        """Should add new showtime"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_response = Mock()
            mock_response.success = True
            mock_response.showtime_id = 'new-id'
            mock_stub.AddShowtime.return_value = mock_response
            
            response = client.post('/showtimes',
                                 data=json.dumps({'movie_id': 3, 'theater_id': 3}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_add_showtime_missing_fields(self, client):
        """Should return 400 for missing required fields"""
        response = client.post('/showtimes',
                             data=json.dumps({'movie_id': 3}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'required' in data['error']


class TestReserveSeat:
    """Test POST /showtimes/<id>/reserve endpoint"""
    
    def test_reserve_seat_success(self, client):
        """Should reserve seat successfully"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_response = Mock()
            mock_response.success = True
            mock_stub.ReserveSeat.return_value = mock_response
            
            response = client.post('/showtimes/1/reserve',
                                 data=json.dumps({'seat': 'A1', 'user': 'TestUser'}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_reserve_seat_missing_fields(self, client):
        """Should return 400 for missing required fields"""
        response = client.post('/showtimes/1/reserve',
                             data=json.dumps({'seat': 'A1'}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestCancelReservation:
    """Test DELETE /showtimes/<id>/reserve endpoint"""
    
    def test_cancel_reservation_success(self, client):
        """Should cancel reservation successfully"""
        with patch('server.routes.showtime.showtime_stub') as mock_stub:
            mock_response = Mock()
            mock_response.success = True
            mock_stub.CancelReservation.return_value = mock_response
            
            response = client.delete('/showtimes/1/reserve',
                                   data=json.dumps({'seat': 'A1'}),
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_cancel_reservation_missing_seat(self, client):
        """Should return 400 for missing seat"""
        response = client.delete('/showtimes/1/reserve',
                               data=json.dumps({}),
                               content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False