import threading
import logging
from typing import List, Optional

from src.models.player import Player


class Battleship:
    def __init__(self):
        self.players: List[Player] = []
        self.game_round = 0

        self.radar_screen = {}  # Store radar screen for each player

        self.lock = threading.Lock()
        self.game_started = False

    def handle_attack(self, attacker: str, target_position: int):
        """
        Handle an attack from a player on the opponent player.

        Args:
            attacker (str): The name of player attacking.
            target_position (int): The position on the board that is being attacked.
        """

        # Map attacker and defender based on the player name
        if attacker == self.players[0].name:
            attacker = self.players[0]
            defender = self.players[1]
        else:
            attacker = self.players[1]
            defender = self.players[0]

        with self.lock:
            if target_position in defender.ships:
                # Hit
                logging.info(f"{attacker.name} hit a ship at position {target_position}.")
                attacker.radar_screen[target_position] = 1
            else:
                attacker.radar_screen[target_position] = -1

        self.game_round += 1

        return attacker.radar_screen

    def check_winner(self):
        """
        Check if there is a winner of the game.
        Returns:
            str or None: The name of the winning player or None if no winner yet.
        """
        # Winner check logic here (e.g., verify if a player's ships are all sunk)
        for p in self.players:
            if p.radar_screen.count(1) == 16:
                return p.name

    def handle_player_init(self, player: Player) -> None:
        """
        Add a player to the game. Start the game automatically when two players are connected.

        Args:
            player (Player): The player to add to the game containing their name and ship configuration.
        """
        with self.lock:
            if len(self.players) == 2:
                logging.error("Game already has two players. Resetting the game.")
                self.handle_game_reset()

            self.players.append(player)
            logging.info(f"Player {player.name} added to the game.")

            # Automatically start game if two players are connected
            if len(self.players) == 2:
                self.start_game()

    def handle_game_reset(self) -> None:
        """
        Reset the game state.
        """
        with self.lock:
            self.players = []
            self.game_round = 0
            logging.info("Game has been reset.")

    def start_game(self) -> None:
        """
        Start the game by setting the game round to 1.
        """
        self.game_started = True
        self.game_round = 1
        logging.info("Game started with two players connected.")
