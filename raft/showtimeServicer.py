import grpc
from time import time

from rpc import showtimes_pb2
from rpc import showtimes_pb2_grpc

class ShowtimesServicer(showtimes_pb2_grpc.ShowtimesServicer):
    """Implementation of the Showtimes service."""
    
    def __init__(self, showtimes, node_address_map):
        self.showtimes = showtimes
        self.node_address_map = node_address_map  # Map of raft_address -> grpc_address
    
    def GetShowtime(self, request, context):
        showtime_data = self.showtimes.get_showtime(request.showtime_id)
        
        if showtime_data is None:
            return showtimes_pb2.GetShowtimeResponse(found=False)
        
        # Create Reservation objects for each reserved seat
        reserved_seats = {}
        for seat, reservation_data in showtime_data.get('reserved_seats', {}).items():
            reserved_seats[seat] = showtimes_pb2.Reservation(
                user=reservation_data.get('user', '')
            )
        
        # Create Showtime object
        showtime = showtimes_pb2.Showtime(
            reserved_seats=reserved_seats,
            movie_id=showtime_data.get('movie_id', 0),
            theater_id=showtime_data.get('theater_id', 0),
            time=showtime_data.get('time', ''),
            price=showtime_data.get('price', 0.0)
        )
        
        return showtimes_pb2.GetShowtimeResponse(showtime=showtime, found=True)
    
    def GetShowtimes(self, request, context):
        try:
            raw_showtimes = self.showtimes.get_showtimes()
            proto_showtimes = {}
            
            for showtime_id, showtime_data in raw_showtimes.items():
                # Create Reservation objects for each reserved seat
                reserved_seats = {}
                for seat, reservation_data in showtime_data.get('reserved_seats', {}).items():
                    reserved_seats[seat] = showtimes_pb2.Reservation(
                        user=reservation_data.get('user', '')
                    )
                
                # Create Showtime object
                proto_showtimes[showtime_id] = showtimes_pb2.Showtime(
                    reserved_seats=reserved_seats,
                    movie_id=showtime_data.get('movie_id', 0),
                    theater_id=showtime_data.get('theater_id', 0),
                    time=showtime_data.get('time', ''),
                    price=showtime_data.get('price', 0.0)
                )
            
            return showtimes_pb2.GetShowtimesResponse(showtimes=proto_showtimes)
        except Exception as e:
            print(f"Error in GetShowtimes: {str(e)}")
            return showtimes_pb2.GetShowtimesResponse(showtimes={})
    
    def AddShowtime(self, request, context):
        # Check if this node is the leader
        if not self.showtimes._isLeader():
            # Forward to leader
            leader = self.showtimes._getLeader()
            if leader is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("No leader elected yet. Please retry.")
                return showtimes_pb2.AddShowtimeResponse(message="No leader available")
            
            # Get leader's gRPC address
            leader_addr = str(leader.address) if hasattr(leader, 'address') else str(leader)
            leader_grpc = self.node_address_map.get(leader_addr)
            
            if not leader_grpc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Leader address mapping not found: {leader_addr}")
                return showtimes_pb2.AddShowtimeResponse(message="Leader address unknown")
            
            print(f"[FOLLOWER] Forwarding request to leader at {leader_grpc}")
            
            # Forward request to leader
            try:
                with grpc.insecure_channel(leader_grpc) as channel:
                    stub = showtimes_pb2_grpc.ShowtimesStub(channel)
                    response = stub.AddShowtime(request)
                    print(f"[FOLLOWER] Received response from leader: {response.message}")
                    return response
            except Exception as e:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(f"Failed to forward to leader: {str(e)}")
                return showtimes_pb2.AddShowtimeResponse(message=f"Forward failed: {str(e)}")
            
        return showtimes_pb2_grpc.AddShowtimeResponse(message="Not implemented yet")
    
    
    def ReserveSeat(self, request, context):
        # Check if this node is the leader
        if not self.showtimes._isLeader():
            # Forward to leader
            leader = self.showtimes._getLeader()
            if leader is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("No leader elected yet. Please retry.")
                return showtimes_pb2.ReserveSeatResponse(message="No leader available")
            
            # Get leader's gRPC address
            leader_addr = str(leader.address) if hasattr(leader, 'address') else str(leader)
            leader_grpc = self.node_address_map.get(leader_addr)
            
            if not leader_grpc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Leader address mapping not found: {leader_addr}")
                return showtimes_pb2.ReserveSeatResponse(message="Leader address unknown")
            
            print(f"[FOLLOWER] Forwarding request to leader at {leader_grpc}")
            
            # Forward request to leader
            try:
                with grpc.insecure_channel(leader_grpc) as channel:
                    stub = showtimes_pb2_grpc.ShowtimesStub(channel)
                    response = stub.ReserveSeat(request)
                    print(f"[FOLLOWER] Received response from leader: {response.message}")
                    return response
            except Exception as e:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(f"Failed to forward to leader: {str(e)}")
                return showtimes_pb2.ReserveSeatResponse(message=f"Forward failed: {str(e)}")
        
        # This node is the leader - process the request
        self.showtimes._increment()
        time.sleep(0.01)  # Allow replication to complete
        count = self.showtimes.get_count()
        
        print(f"[LEADER] Received: {request.message} (Count: {count})")
        response_message = f"Pong! (received: '{request.message}', count: {count})"
        print(f"[LEADER] Sending: {response_message}")
        return showtimes_pb2.ReserveSeatResponse(message=response_message)
    
    def CancelReservation(self, request, context):
        # Check if this node is the leader
        if not self.showtimes._isLeader():
            # Forward to leader
            leader = self.showtimes._getLeader()
            if leader is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("No leader elected yet. Please retry.")
                return showtimes_pb2.CancelReservationResponse(message="No leader available")
            
            # Get leader's gRPC address
            leader_addr = str(leader.address) if hasattr(leader, 'address') else str(leader)
            leader_grpc = self.node_address_map.get(leader_addr)
            
            if not leader_grpc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Leader address mapping not found: {leader_addr}")
                return showtimes_pb2.CancelReservationResponse(message="Leader address unknown")
            
            print(f"[FOLLOWER] Forwarding request to leader at {leader_grpc}")
            
            # Forward request to leader
            try:
                with grpc.insecure_channel(leader_grpc) as channel:
                    stub = showtimes_pb2_grpc.ShowtimesStub(channel)
                    response = stub.CancelReservation(request)
                    print(f"[FOLLOWER] Received response from leader: {response.message}")
                    return response
            except Exception as e:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(f"Failed to forward to leader: {str(e)}")
                return showtimes_pb2.CancelReservationResponse(message=f"Forward failed: {str(e)}")
            
        response_message = f"CancelReservation not implemented yet."
        print(f"[LEADER] Sending: {response_message}")
        return showtimes_pb2.CancelReservationResponse(message="Not implemented yet")