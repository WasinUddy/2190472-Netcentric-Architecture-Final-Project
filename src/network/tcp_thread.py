import json
import socket
import logging
import websockets
import asyncio
from threading import Thread

from src.models.player import Player


class TCPThread(Thread):
    def __init__(self, host: str, port: int, game_instance, web_uri: str = 'ws://127.0.0.1:1001'):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.game_instance = game_instance
        self.web_uri = web_uri
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(2)
        self.socket.settimeout(1)
        self.connections = {}
        self.winner_declared = False

        logging.info(f"TCPThread initialized on {self.host}:{self.port}")

    def run(self):
        logging.info("TCPThread started, waiting for player connections...")
        while True:
            try:
                conn, addr = self.socket.accept()
                logging.info(f"New connection accepted from {addr}")
                Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

    def _handle_connection(self, conn, addr):
        logging.info(f"Handling connection from {addr}")
        while True:
            try:
                payload = json.loads(conn.recv(2048).decode('utf-8'))
                reply = {}
                author = payload.get('author', 'Unknown')

                if author and author not in self.connections:
                    self.connections[author] = conn
                    logging.info(f"Player {author} connected from {addr}")

                if payload['header'] == 'init':
                    player = Player(name=payload['author'], ships=payload['body'])
                    self.game_instance.handle_player_init(player)
                    logging.info(f"Player {payload['author']} initialized with ships")

                    # Trigger WebSocket broadcast after player initialization
                    self.trigger_websocket_broadcast()

                elif payload['header'] == 'game' and payload['body'] == 'round':
                    reply = {
                        'header': 'game',
                        'body': self.game_instance.game_round,
                        'names': {
                            'A': self.game_instance.players[0].name,
                            'B': self.game_instance.players[1].name
                        }
                    }
                    logging.info(f"Round information sent to player {author}")

                    # Trigger WebSocket broadcast after sending round info
                    self.trigger_websocket_broadcast()

                elif payload['header'] == 'game':
                    target_position = int(payload['body'][0])
                    result_rad = self.game_instance.handle_attack(author, target_position)
                    reply = {'header': 'game', 'body': result_rad}
                    logging.info(f"Player {author} attacked position {target_position}")

                    # Trigger WebSocket broadcast after an attack
                    self.trigger_websocket_broadcast()

                # Check for Winner after every operation
                winner = self.game_instance.check_winner()
                if winner and not self.winner_declared:
                    self.broadcast({'header': 'game_over', 'body': winner})
                    self.winner_declared = True
                    logging.info(f"Game over! Winner: {winner}")

                    # Trigger WebSocket broadcast after game over
                    self.trigger_websocket_broadcast()

                # Send reply to the client
                conn.sendall(json.dumps(reply).encode('utf-8'))

            except (socket.error, UnicodeDecodeError, json.JSONDecodeError) as e:
                logging.error(f"Error handling connection from {addr}: {e}")
                break

            except Exception as e:
                logging.error(f"Unexpected error handling connection from {addr}: {e}")
                break

        logging.info(f"Connection from {addr} closed")

    def broadcast(self, payload):
        logging.info("Broadcasting message to all connected players")
        for author, conn in self.connections.items():
            try:
                conn.sendall(json.dumps(payload).encode('utf-8'))
                logging.info(f"Broadcasted message to {author}")
            except Exception as e:
                logging.error(f"Failed to send broadcast to {author}: {e}")

        self.trigger_websocket_broadcast()  # Trigger after broadcasting

    def trigger_websocket_broadcast(self):
        logging.info("Triggering websocket broadcast")
        try:
            payload = {
                'command': 'broadcast',
                'player1Score': self.game_instance.players[0].radar_screen.count(1),
                'player2Score': self.game_instance.players[1].radar_screen.count(1),
                'player1Name': self.game_instance.players[0].name,
                'player2Name': self.game_instance.players[1].name,
                'winner': self.game_instance.check_winner()  # Assuming this returns the winner's name or None
            }
            asyncio.run(self._websocket_broadcast(payload))
        except Exception as e:
            logging.error(f"Error running websocket broadcast: {e}")

    async def _websocket_broadcast(self, payload):
        try:
            async with websockets.connect(self.web_uri) as websocket:
                await websocket.send(json.dumps(payload))
                logging.info("Sent broadcast trigger to WebSocket server")
                response = await websocket.recv()  # Optionally, handle server response if needed
                logging.info(f"Received response from WebSocket server: {response}")
        except Exception as e:
            logging.error(f"Failed to trigger websocket broadcast: {e}")
