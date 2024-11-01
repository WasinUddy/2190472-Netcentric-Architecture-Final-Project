import threading
import logging
from typing import List
from src.models.player import Player


class Battleship:

    def __init__(self):
        self.players: List[Player] = []
        self.game_round = 0 

        self.lock = threading.Lock()

    def handle_add_player(self, player: Player):
        """
        Handle adding a player to the game and trigger the start of the game if there are two players

        Args:
            player (Player): The player to add to the game containing their name and ship configuration
        """
        if len(self.players) == 2:
            logging.error('Game already has two players and cannot accept more resetting the game')
            self.handle_game_reset()
        
        self.players.append(player)
        if len(self.players) == 2:
            self.start_game()

    def handle_game_reset(self):
        """
        Handle resetting the game state
        """
        self.players = []
        self.game_round = 0

    def start_game(self):
        self.game_round = 1



        