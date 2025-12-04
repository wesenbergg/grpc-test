from pysyncobj import SyncObj, replicated
import uuid

class GlobalState(SyncObj):
    """Replicated counter using Raft consensus."""
    
    def __init__(self, selfAddress, partnerAddrs):
        super(GlobalState, self).__init__(selfAddress, partnerAddrs)
        self.__counter = 0
        self.__showtimes = { 
            '1': {
                "reserved_seats": { "A1": { "user": "Adam" } },
                "movie_id": 1,
                "theater_id": 1,
                "time": "2024-07-01T19:00:00",
                "price": 12.50,
            },
            '2': {
                "reserved_seats": { "B2": { "user": "Eve" } },
                "movie_id": 2,
                "theater_id": 2,
                "time": "2024-07-01T21:00:00",
                "price": 15.00,
            }
    }
    
    """
    Ping-Pong counter methods
    """

    @replicated
    def _increment(self):
        self.__counter += 1
        # Log on followers when state is replicated
        if not self._isLeader():
            print(f"[FOLLOWER] Replicated state update - Counter now: {self.__counter}")
    
    def get_count(self):
        return self.__counter
    
    """
    Showtimes methods
    """
    
    def get_showtimes(self):
        return self.__showtimes
    
    def get_showtime(self, showtime_id):
        return self.__showtimes.get(showtime_id, None)
    
    @replicated
    def add_showtime(self, movie_id, theater_id):
        """Add a new showtime."""
        showtime_id = str(uuid.uuid4())
        if showtime_id not in self.__showtimes:
            self.__showtimes[showtime_id] = {
                "reserved_seats": {},
                "movie_id": movie_id,
                "theater_id": theater_id,
                "time": "2024-07-01T20:00:00",
                "price": 10.0,
            }
            # Log on followers when state is replicated
            if not self._isLeader():
                print(f"[FOLLOWER] Replicated state update - Added showtime {showtime_id}")
            return True
        return False

    @replicated
    def reserve_seat(self, showtime_id, seat, user):
        """Reserve a seat for a user in a specific showtime."""
        if showtime_id in self.__showtimes:
            self.__showtimes[showtime_id]['reserved_seats'][seat] = { "user": user }
            # Log on followers when state is replicated
            if not self._isLeader():
                print(f"[FOLLOWER] Replicated state update - Reserved seat {seat} for {user} in showtime {showtime_id}")
            return True
        return False
    
    @replicated
    def cancel_reservation(self, showtime_id, seat):
        """Cancel a seat reservation for a specific showtime."""
        if showtime_id in self.__showtimes and seat in self.__showtimes[showtime_id]['reserved_seats']:
            del self.__showtimes[showtime_id]['reserved_seats'][seat]
            # Log on followers when state is replicated
            if not self._isLeader():
                print(f"[FOLLOWER] Replicated state update - Canceled reservation for seat {seat} in showtime {showtime_id}")
            return True
        return False
