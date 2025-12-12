"""
Pytest configuration and shared fixtures
"""
import pytest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_sync_obj():
    """Mock SyncObj for testing GlobalState without actual Raft coordination"""
    mock = Mock()
    mock._isLeader.return_value = True
    mock._getLeader.return_value = None
    return mock


@pytest.fixture
def mock_grpc_context():
    """Mock gRPC context for servicer testing"""
    context = Mock()
    context.set_code = Mock()
    context.set_details = Mock()
    return context


@pytest.fixture
def mock_grpc_channel():
    """Mock gRPC channel for client testing"""
    return MagicMock()


@pytest.fixture
def sample_showtime_data():
    """Sample showtime data for testing"""
    return {
        'reserved_seats': {'A1': {'user': 'TestUser'}},
        'movie_id': 1,
        'theater_id': 1,
        'time': '2024-07-01T19:00:00',
        'price': 12.50
    }
