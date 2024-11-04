import json
import socket
import logging
import websockets
import asyncio
from threading import Thread

from src.core.battleship import Battleship
from src.models.player import Player


class TCPThread(Thread):
    def __init__(self, host: str, port: int, game_instance: Battleship, web_uri: str = 'ws://127.0.0.1:1001'):
        super().__init__(daemon=True)  # Avoid zombie threads

        self.host = host
        self.port = port
        self.game_instance = game_instance

        self.web_uri = web_uri
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(2)
        self.socket.settimeout(1)
        self.connections = {}

        self.winner_declared = False  # To prevent multiple game over messages

    def run(self):
        while True:
            try:
                # Accept new connection
                conn, addr = self.socket.accept()
                Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                pass

    def _handle_connection(self, conn, addr):
        """
        Handle individual connections in a separate thread
        """

        while True:
            try:
                payload = json.loads(conn.recv(2048).decode('utf-8'))
                reply = {}

                author = payload['author']

                # First registration to the game from first connection
                if author and author not in self.connections:
                    self.connections[author] = conn  # Store connection for future use (e.g., broadcast)
                    logging.info(f"Player {author} connected from {addr}")

                # Handle game initialization
                if payload['header'] == 'init':
                    player = Player(name=payload['author'], ships=payload['body'])
                    self.game_instance.handle_player_init(player)

                # Handle Round Number Request
                elif payload['header'] == 'game' and payload['body'] == 'round':
                    reply = {
                        'header': 'game',
                        'body': self.game_instance.game_round,
                        'names': {  # To maintain legacy compatibility
                            'A': self.game_instance.players[0].name,
                            'B': self.game_instance.players[1].name
                        }
                    }

                # Handle Game Attack
                elif payload['header'] == 'game':
                    target_position = int(payload['body'][0])
                    result_rad = self.game_instance.handle_attack(author, target_position)
                    reply = {'header': 'game', 'body': result_rad}

                # Check for Winner after every operation
                winner = self.game_instance.check_winner()
                if winner:
                    if not self.winner_declared:
                        self.broadcast({'header': 'game_over', 'body': winner})
                        self.winner_declared = True

                # Send reply to the client
                conn.sendall(json.dumps(reply).encode('utf-8'))

            except socket.error as e:
                logging.error(f"Error handling connection: {e}")
                break

            except UnicodeDecodeError as e:
                logging.error(f"Error decoding message: {e}")
                continue

            except json.JSONDecodeError:
                continue

    def broadcast(self, payload):
        """
        Broadcast a payload to all clients connected to the server

        Args:
            payload (dict): The payload to broadcast to all clients
        """
        for c in self.connections.values():
            c.sendall(json.dumps(payload).encode('utf-8'))

        # Trigger websocket broadcast after sending TCP broadcast
        self.trigger_websocket_broadcast()

    def trigger_websocket_broadcast(self):
        """
        Triggers the websocket broadcast using asyncio.
        """
        asyncio.run(self._websocket_broadcast())

    async def _websocket_broadcast(self):
        """
        The asynchronous method to handle websocket broadcasting.
        """
        try:
            async with websockets.connect(self.web_uri) as websocket:
                await websocket.send(json.dumps({'command': 'broadcast'}))
                await websocket.recv()  # Optionally, handle server response if needed
        except Exception as e:
            logging.error(f"Failed to trigger websocket broadcast: {e}")