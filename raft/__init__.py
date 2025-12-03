"""Raft consensus module for distributed counter and showtimes."""

from .state import GlobalState
from .pingServicer import PingPongServicer

__all__ = ['GlobalState', 'PingPongServicer']
