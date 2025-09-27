# WebSocket extension for typing commands
# Add this to slywriter_server.py or import it

from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import random

def init_websocket(app):
    """Initialize WebSocket support for the Flask app"""
    socketio = SocketIO(app,
                       cors_allowed_origins="*",
                       async_mode='eventlet',
                       logger=True,
                       engineio_logger=True)

    @socketio.on('connect')
    def handle_connect():
        print(f'[WS] Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to typing server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'[WS] Client disconnected: {request.sid}')

    @socketio.on('type_text')
    def handle_type_text(data):
        """
        Receive text from client, process it, and send back typing commands
        """
        text = data.get('text', '')
        settings = data.get('settings', {})
        user_id = data.get('user_id')

        print(f'[WS] Typing request from {user_id}: {len(text)} chars')

        # Process text and send typing commands
        for i, char in enumerate(text):
            # Calculate realistic delay
            base_delay = settings.get('speed', 60)  # WPM
            delay = calculate_typing_delay(char, base_delay)

            # Send typing command to client
            emit('type_char', {
                'char': char,
                'index': i,
                'delay': delay,
                'total': len(text)
            })

            # Small server-side delay to prevent flooding
            time.sleep(0.01)

        # Send completion signal
        emit('typing_complete', {'total_chars': len(text)})

    @socketio.on('pause_typing')
    def handle_pause():
        """Pause typing on client"""
        emit('pause_command', {'paused': True})

    @socketio.on('resume_typing')
    def handle_resume():
        """Resume typing on client"""
        emit('resume_command', {'resumed': True})

    @socketio.on('stop_typing')
    def handle_stop():
        """Stop typing on client"""
        emit('stop_command', {'stopped': True})

    return socketio

def calculate_typing_delay(char, base_wpm):
    """
    Calculate realistic typing delay based on character and WPM
    """
    # Convert WPM to base delay in ms
    base_delay = 60000 / (base_wpm * 5)  # Average word = 5 chars

    # Add variation based on character type
    if char in '.!?':
        delay = base_delay * random.uniform(2.0, 3.0)  # Longer pause after sentences
    elif char in ',;:':
        delay = base_delay * random.uniform(1.5, 2.0)  # Medium pause after clauses
    elif char == ' ':
        delay = base_delay * random.uniform(0.8, 1.2)  # Normal space
    elif char.isupper():
        delay = base_delay * random.uniform(1.1, 1.4)  # Slightly slower for capitals
    else:
        delay = base_delay * random.uniform(0.7, 1.3)  # Normal variation

    return int(delay)

# Usage in slywriter_server.py:
# from websocket_typing import init_websocket
# socketio = init_websocket(app)
#
# Then at the bottom of the file:
# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=5000, debug=True)