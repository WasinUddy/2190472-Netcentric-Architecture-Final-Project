import threading
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

        Raises:
            ValueError: If the game already has two players
        """
        if len(self.players) == 2:
            raise ValueError('Battleship game can only have two players')
        
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



        