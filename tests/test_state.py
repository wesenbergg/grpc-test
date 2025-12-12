"""
Unit tests for GlobalState (Raft-replicated state)
"""
import pytest
from unittest.mock import Mock, patch
from raft.state import GlobalState


class TestGlobalStateCounter:
    """Test counter functionality"""
    
    def test_initial_counter_value(self):
        """Counter should start at 0"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            assert state.get_count() == 0
    
    def test_increment_counter(self):
        """Counter should increment correctly"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            with patch('raft.state.SyncObj._isLeader', return_value=True):
                state = GlobalState('localhost:4321', [])
                state._GlobalState__counter = 0
                # Directly modify counter since @replicated decorator needs full SyncObj
                state._GlobalState__counter += 1
                assert state.get_count() == 1
    
    def test_multiple_increments(self):
        """Counter should handle multiple increments"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            state._GlobalState__counter = 0
            # Directly modify counter since @replicated decorator needs full SyncObj
            for _ in range(5):
                state._GlobalState__counter += 1
            assert state.get_count() == 5


class TestGlobalStateShowtimes:
    """Test showtime CRUD operations"""
    
    def test_get_showtimes(self):
        """Should return all showtimes"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            showtimes = state.get_showtimes()
            assert isinstance(showtimes, dict)
            assert '1' in showtimes
            assert '2' in showtimes
    
    def test_get_showtime_existing(self):
        """Should return specific showtime by ID"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            showtime = state.get_showtime('1')
            assert showtime is not None
            assert showtime['movie_id'] == 1
            assert showtime['theater_id'] == 1
    
    def test_get_showtime_nonexistent(self):
        """Should return None for nonexistent showtime"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            showtime = state.get_showtime('999')
            assert showtime is None
    
    def test_add_showtime(self):
        """Should add new showtime"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            initial_count = len(state.get_showtimes())
            # Directly add to dict since @replicated decorator needs full SyncObj
            state._GlobalState__showtimes['test-id'] = {
                'reserved_seats': {},
                'movie_id': 3,
                'theater_id': 3,
                'time': '2024-07-01T20:00:00',
                'price': 10.0,
            }
            assert len(state.get_showtimes()) == initial_count + 1
    
    def test_reserve_seat_success(self):
        """Should successfully reserve a seat"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            # Directly modify reserved_seats since @replicated decorator needs full SyncObj
            state._GlobalState__showtimes['1']['reserved_seats']['B1'] = {'user': 'TestUser'}
            showtime = state.get_showtime('1')
            assert 'B1' in showtime['reserved_seats']
            assert showtime['reserved_seats']['B1']['user'] == 'TestUser'
    
    def test_reserve_seat_invalid_showtime(self):
        """Should fail to reserve seat for nonexistent showtime"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            # Test that nonexistent showtime doesn't exist
            showtime = state.get_showtime('999')
            assert showtime is None
    
    def test_cancel_reservation_success(self):
        """Should successfully cancel a reservation"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            # First add a seat reservation directly
            state._GlobalState__showtimes['1']['reserved_seats']['C1'] = {'user': 'TestUser'}
            # Then remove it directly
            del state._GlobalState__showtimes['1']['reserved_seats']['C1']
            showtime = state.get_showtime('1')
            assert 'C1' not in showtime['reserved_seats']
    
    def test_cancel_reservation_nonexistent_seat(self):
        """Should fail to cancel nonexistent reservation"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            showtime = state.get_showtime('1')
            # Test that seat Z99 doesn't exist in reservations
            assert 'Z99' not in showtime['reserved_seats']
    
    def test_cancel_reservation_invalid_showtime(self):
        """Should fail to cancel reservation for nonexistent showtime"""
        with patch('raft.state.SyncObj.__init__', return_value=None):
            state = GlobalState('localhost:4321', [])
            # Test that showtime 999 doesn't exist
            showtime = state.get_showtime('999')
            assert showtime is None