import json
import socket
import logging

from src.core.battleship import Battleship
from src.models.player import Player

class TCPThread:
    def __init__(self, host: str, port: int, game_instance: Battleship):
        self.host = host
        self.port = port
        self.game_instance = game_instance

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(2)
        self.socket.settimeout(1)

    
    def run(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                payload = json.loads(conn.recv(2048).decode('utf-8'))

                if payload['header'] == 'init':
                    self._handle_init(payload)
                    logging.info(f'Player {payload["client"]}, {addr} has joined the game')

                elif payload['header'] == 'restart':
                    self._handle_restart()
                    logging.info('Game has been restarted')


            except socket.timeout:
                pass


    def _handle_init(self, payload):
        """
        Handle the initialization of a player in the game adding them to the game instance

        Args:
            payload (dict): The payload containing the client name and ship configuration
        """
        player = Player(
            name=payload['client'],
            ships=payload['body']
        )

        with self.game_instance.lock:
            self.game_instance.handle_add_player(player)


    def _handle_request_current_round(self):
        """
        Handle the request for the current round of the game
        """
        with self.game_instance.lock:
            return self.game_instance.game_round
        
    
    def _handle_restart(self):  
        """
        Handle the restart of the game resetting the game state
        """
        with self.game_instance.lock:
            self.game_instance.handle_game_reset()
