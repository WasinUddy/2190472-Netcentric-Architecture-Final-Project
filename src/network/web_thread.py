import json
import asyncio
import logging

import websockets
from threading import Thread

from src.core.battleship import Battleship

class WebThread(Thread):
    def __init__(self, host: str, port: int, game_instance: Battleship):
        super().__init__(daemon=True)

        self.host = host
        self.port = port
        self.game_instance = game_instance
        self.connections = set()

    async def run(self):
        async with websockets.serve(self._handle_connection, self.host, self.port):
            logging.info(f"Websocket server started at {self.host}:{self.port}")
            await asyncio.Future()

    async def _handle_connection(self, websocket):
        self.connections.add(websocket)
        logging.info(f"New connection from {websocket.remote_address}")

        try:
            await websocket.send("Connected to the server.")
            async for message in websocket:
                payload = json.loads(message)
                await self._handle_payload(payload)
        except websockets.ConnectionClosed:
            logging.info(f"Connection closed by {websocket.remote_address}")
        finally:
            self.connections.remove(websocket)
            logging.info(f"Connection removed from {websocket.remote_address}")

    async def _handle_payload(self, payload):
        if payload['command'] == 'reset':
            self.game_instance.handle_game_reset()

        # Broadcast game state trigger from TCPThread
        elif payload['command'] == 'broadcast':
            await self.broadcast_game_state()

    async def broadcast_game_state(self):
        game_state = {
            'player1Score': self.game_instance.players[0].radar_screen.count(1),
            'player2Score': self.game_instance.players[1].radar_screen.count(1),
            'player1Name': self.game_instance.players[0].name,
            'player2Name': self.game_instance.players[1].name,
            'gameRound': self.game_instance.game_round,
            'winner': self.game_instance.check_winner()
        }
        for connection in self.connections:
            await connection.send(json.dumps(game_state))