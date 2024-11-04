import logging
from src.core.battleship import Battleship
from src.network.tcp_thread import TCPThread
from src.network.web_thread import WebThread

logging.basicConfig(level=logging.INFO)

# Initialize the game instance
game_instance = Battleship()

# Create the WebThread for WebSocket communication
web_thread = WebThread(
    host='0.0.0.0',  # Replace with your actual IP
    port=1000,
    game_instance=game_instance
)

# Create the TCPThread for TCP communication
tcp_thread = TCPThread(
    host='0.0.0.0',  # Replace with your actual IP
    port=1001,
    game_instance=game_instance,
    web_uri='ws://127.0.0.1:1000'  # WebSocket URI to communicate with WebThread
)

# Start both threads concurrently
web_thread.start()  # Start the WebSocket server
tcp_thread.start()  # Start the TCP server

# Join both threads to keep the main program running
web_thread.join()
tcp_thread.join()
