#!/usr/bin/env python3
"""
Showtime Router - Showtime management endpoints
"""
from flask import Blueprint, jsonify, request
import grpc

from rpc import showtimes_pb2, showtimes_pb2_grpc

showtime_bp = Blueprint('showtimes', __name__)

# gRPC client connection
channel = grpc.insecure_channel('localhost:50051')
showtime_stub = showtimes_pb2_grpc.ShowtimesStub(channel)


@showtime_bp.route('/showtimes', methods=['GET'])
def get_showtimes():
    """Get all showtimes"""
    try:
        grpc_request = showtimes_pb2.GetShowtimesRequest()
        grpc_response = showtime_stub.GetShowtimes(grpc_request)
        
        # Convert protobuf map to dict
        showtimes = {}
        for showtime_id, showtime in grpc_response.showtimes.items():
            reserved_seats = {}
            for seat, reservation in showtime.reserved_seats.items():
                reserved_seats[seat] = {'user': reservation.user}
            
            showtimes[showtime_id] = {
                'reserved_seats': reserved_seats,
                'movie_id': showtime.movie_id,
                'theater_id': showtime.theater_id,
                'time': showtime.time,
                'price': showtime.price
            }
        
        return jsonify({
            'success': True,
            'showtimes': showtimes
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


@showtime_bp.route('/showtimes/<showtime_id>', methods=['GET'])
def get_showtime(showtime_id):
    """Get a specific showtime by ID"""
    try:
        grpc_request = showtimes_pb2.GetShowtimeRequest(showtime_id=showtime_id)
        grpc_response = showtime_stub.GetShowtime(grpc_request)
        
        if not grpc_response.found:
            return jsonify({
                'success': False,
                'error': 'Showtime not found'
            }), 404
        
        # Convert protobuf to dict
        showtime = grpc_response.showtime
        reserved_seats = {}
        for seat, reservation in showtime.reserved_seats.items():
            reserved_seats[seat] = {'user': reservation.user}
        
        return jsonify({
            'success': True,
            'showtime': {
                'reserved_seats': reserved_seats,
                'movie_id': showtime.movie_id,
                'theater_id': showtime.theater_id,
                'time': showtime.time,
                'price': showtime.price
            }
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


@showtime_bp.route('/showtimes', methods=['POST'])
def add_showtime():
    """Add a new showtime"""
    try:
        data = request.get_json()
        
        if not data or 'movie_id' not in data or 'theater_id' not in data:
            return jsonify({
                'success': False,
                'error': 'movie_id and theater_id are required'
            }), 400
        
        grpc_request = showtimes_pb2.AddShowtimeRequest(
            movie_id=data['movie_id'],
            theater_id=data['theater_id']
        )
        grpc_response = showtime_stub.AddShowtime(grpc_request)
        
        return jsonify({
            'success': grpc_response.success,
            'showtime_id': grpc_response.showtime_id
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


@showtime_bp.route('/showtimes/<showtime_id>/reserve', methods=['POST'])
def reserve_seat(showtime_id):
    """Reserve a seat in a showtime"""
    try:
        data = request.get_json()
        
        if not data or 'seat' not in data or 'user' not in data:
            return jsonify({
                'success': False,
                'error': 'seat and user are required'
            }), 400
        
        grpc_request = showtimes_pb2.ReserveSeatRequest(
            showtime_id=showtime_id,
            seat=data['seat'],
            user=data['user']
        )
        grpc_response = showtime_stub.ReserveSeat(grpc_request)
        
        return jsonify({
            'success': grpc_response.success
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


@showtime_bp.route('/showtimes/<showtime_id>/reserve', methods=['DELETE'])
def cancel_reservation(showtime_id):
    """Cancel a seat reservation"""
    try:
        data = request.get_json()
        
        if not data or 'seat' not in data:
            return jsonify({
                'success': False,
                'error': 'seat is required'
            }), 400
        
        grpc_request = showtimes_pb2.CancelReservationRequest(
            showtime_id=showtime_id,
            seat=data['seat']
        )
        grpc_response = showtime_stub.CancelReservation(grpc_request)
        
        return jsonify({
            'success': grpc_response.success
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
