import json
import random
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

        self.pa = None
        self.pb = None

        logging.info(f"TCPThread initialized on {self.host}:{self.port}")

    def run(self):
        logging.info("TCPThread started, waiting for player connections...")

        # Start the _reset_listener as an independent asyncio task
        asyncio.run(self._start_async_tasks())

    async def _start_async_tasks(self):
        # Create a task for _reset_listener so it can run concurrently
        reset_task = asyncio.create_task(self._reset_listener())

        # Main connection loop, using asyncio for non-blocking behavior
        while True:
            try:
                conn, addr = await asyncio.to_thread(self.socket.accept)
                logging.info(f"New connection accepted from {addr}")
                Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error accepting connection: {e}", exc_info=True)

    def _handle_connection(self, conn, addr):
        logging.info(f"Handling connection from {addr}")

        try:
            # Send initial message to the client to confirm connection
            conn.sendall(json.dumps({'header': 'msg', 'body': 'saygex'}).encode('utf-8'))
            logging.debug(f"Sent initial connection confirmation to {addr}")
        except Exception as e:
            logging.error(f"Error sending initial message to {addr}: {e}", exc_info=True)
            return

        while True:
            try:
                received = conn.recv(2048).decode('utf-8')
                payload = json.loads(received)
                logging.info(f"Received message from {payload.get('author', 'Unknown')} at {addr}: {payload}")
                author = payload.get('author', 'Unknown')

                winner = self.game_instance.check_winner()
                if winner and not self.winner_declared:
                    self.broadcast({'header': 'game_over', 'body': winner})
                    self.winner_declared = True
                    with self.game_instance.lock:
                        self.game_instance.winner_history.append(winner)
                    logging.info(f"Game over, winner: {winner}")

                if author and author not in self.connections:
                    self.connections[author] = conn
                    logging.info(f"Player {author} connected from {addr}")

                if self.connections == {}:
                    logging.info("No players connected, ABORTING")
                    break

                if payload['header'] == 'init':
                    player = Player(name=payload['author'], ships=payload['body'])
                    self.game_instance.handle_player_init(player)
                    logging.info(f"Player {payload['author']} initialized with ships {payload['body']}")

                    self.trigger_websocket_broadcast()

                    if len(self.game_instance.players) == 2:
                        if not self.pa or not self.pb:
                            self.pa = random.choice([0, 1])
                            self.pb = abs(self.pa - 1)

                        if len(self.game_instance.winner_history) > 0 and self.game_instance.winner_history[-1] != self.game_instance.players[self.pa].name:
                            self.pa, self.pb = self.pb, self.pa

                        init_msg = {
                            'header': 'init',
                            'body': {
                                self.game_instance.players[self.pa].name: 'A',
                                self.game_instance.players[self.pb].name: 'B'
                            }
                        }
                        self.broadcast(init_msg)
                        logging.info(f"Game initialized: {init_msg}")

                elif payload['header'] == 'round':
                    reply = {
                        'header': 'round',
                        'body': self.game_instance.game_round,
                        'names': {
                            'A': self.game_instance.players[self.pa].name,
                            'B': self.game_instance.players[self.pb].name
                        }
                    }
                    logging.info(f"Round information prepared for {author}: {reply}")
                    self._reply(conn, reply)

                    self.trigger_websocket_broadcast()

                elif payload['header'] == 'game':
                    target_position = int(payload['body'][0])
                    result_rad = self.game_instance.handle_attack(author, target_position)
                    self.broadcast({'header': 'game', 'body': result_rad})

                    logging.info(f"Player {author} attacked position {target_position}, result: {result_rad}")

                    self.trigger_websocket_broadcast()

                elif payload['header'] == 'reset':
                    # Check if we got a winner
                    self.trigger_websocket_broadcast()
                    self.game_instance.handle_game_reset()
                    self.broadcast({'header': 'reset'})
                    self.winner_declared = False

                    logging.info("Game reset")

                    # Clear the connections dict
                    self.connections = {}
                    break


            except ConnectionAbortedError:
                self.connections = {}
                logging.info(f"Connection aborted by {addr}")
                break

            except json.JSONDecodeError as e:
                #logging.error(f"JSON decoding error from {addr}: {received}", exc_info=True)
                continue
            except Exception as e:
                logging.error(f"Unexpected error handling connection from {addr}: {e}", exc_info=True)
                continue

        logging.info(f"Connection from {addr} closed")

    def _reply(self, conn, payload):
        conn.sendall(json.dumps(payload).encode('utf-8'))
        logging.info(f"Sent reply to {conn.getpeername()}: {payload}")

    def broadcast(self, payload):
        for author, conn in self.connections.items():
            try:
                conn.sendall(json.dumps(payload).encode('utf-8'))
                logging.info(f"Broadcasted message to {author}: {payload}")
            except Exception as e:
                logging.error(f"Failed to send broadcast to {author}: {e}", exc_info=True)

    def trigger_websocket_broadcast(self):
        logging.info("Triggering websocket broadcast")
        try:
            payload = {
                'command': 'broadcast',
                'player1Score': self.game_instance.players[self.pa].radar_screen.count(1),
                'player2Score': self.game_instance.players[self.pb].radar_screen.count(1),
                'player1Name': self.game_instance.players[self.pa].name,
                'player2Name': self.game_instance.players[self.pb].name,
                'winner': self.game_instance.check_winner(),
                'winner_history': self.game_instance.winner_history
            }
            asyncio.run(self._websocket_broadcast(payload))
        except Exception as e:
            logging.error(f"Error running websocket broadcast: {e}", exc_info=True)

    async def _websocket_broadcast(self, payload):
        try:
            async with websockets.connect(self.web_uri) as websocket:
                await websocket.send(json.dumps(payload))
                logging.info(f"Sent WebSocket broadcast: {payload}")
                response = await websocket.recv()
                logging.info(f"Received WebSocket response: {response}")
        except Exception as e:
            logging.error(f"Failed to trigger websocket broadcast: {e}", exc_info=True)

    async def _reset_listener(self):
        while True:
            await asyncio.sleep(1)
            if self.game_instance.resetted:
                self.game_instance.resetted = False
                self.broadcast({'header': 'reset'})
                logging.info("Game reset broadcasted")

                # Clear the connections dict
                self.connections = {}
                self.winner_declared = False
