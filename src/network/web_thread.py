import asyncio
import websockets
import json
import logging
from threading import Thread


class WebThread(Thread):
    def __init__(self, host: str, port: int, game_instance):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.game_instance = game_instance
        self.connections = set()
        self.loop = None

        logging.info(f"WebThread initialized on {self.host}:{self.port}")

    def run(self):
        # Initialize and start the asyncio event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        logging.info("WebThread event loop started")
        self.loop.run_until_complete(self.start_server())

    async def start_server(self):
        async with websockets.serve(self._handle_connection, self.host, self.port):
            logging.info(f"WebSocket server started at {self.host}:{self.port}")
            await asyncio.Future()  # Keep the server running

    async def _handle_connection(self, websocket):
        self.connections.add(websocket)
        logging.info(f"New WebSocket connection from {websocket.remote_address}")

        try:
            await websocket.send("Connected to the server.")
            async for message in websocket:
                logging.info(f"Message received from {websocket.remote_address}: {message}")
                payload = json.loads(message)
                await self._handle_payload(payload)
        except websockets.ConnectionClosed:
            logging.info(f"Connection closed by {websocket.remote_address}")
        except Exception as e:
            logging.error(f"Error in WebSocket connection: {e}")
        finally:
            self.connections.remove(websocket)
            logging.info(f"Connection removed from {websocket.remote_address}")

    async def _handle_payload(self, payload):
        try:
            if payload['command'] == 'reset':
                logging.info("Received 'reset' command, resetting game")
                self.game_instance.handle_game_reset()
            elif payload['command'] == 'broadcast':
                logging.info("Received 'broadcast' command, broadcasting game state")
                await self.broadcast_game_state()
        except KeyError:
            logging.error(f"Invalid payload received: {payload} - missing 'command' key")
        except Exception as e:
            logging.error(f"Error handling payload: {e}")

    async def broadcast_game_state(self):
        logging.info("Broadcasting game state to all connected clients")
        game_state = {
            'player1Score': self.game_instance.players[0].radar_screen.count(1),
            'player2Score': self.game_instance.players[1].radar_screen.count(1),
            'player1Name': self.game_instance.players[0].name,
            'player2Name': self.game_instance.players[1].name,
            'gameRound': self.game_instance.game_round,
            'winner': self.game_instance.check_winner()
        }
        for connection in self.connections:
            try:
                await connection.send(json.dumps(game_state))
                logging.info(f"Sent game state to {connection.remote_address}")
            except Exception as e:
                logging.error(f"Error sending game state to {connection.remote_address}: {e}")
