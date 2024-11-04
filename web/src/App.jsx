import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BattleshipGame = () => {
  const [player1Score, setPlayer1Score] = useState();
  const [player2Score, setPlayer2Score] = useState(0);
  const [isResetting, setIsResetting] = useState(false);
  const [winner, setWinner] = useState(null);
  const [player1Name, setPlayer1Name] = useState('Player 1');
  const [player2Name, setPlayer2Name] = useState('Player 2');

  const ws = useRef(null); // Use ref to store WebSocket instance

  useEffect(() => {
    // Establish WebSocket connection when the component mounts
    const wsUrl = window.WS_URL || 'ws://localhost:1001';
    ws.current = new WebSocket(wsUrl);

    // WebSocket message listener
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Message from server:', data);

      // Handle incoming broadcast of game state
      if (data.player1Score !== undefined && data.player2Score !== undefined) {
        setPlayer1Score(data.player1Score);
        setPlayer2Score(data.player2Score);
        setPlayer1Name(data.player1Name);
        setPlayer2Name(data.player2Name);
        setWinner(data.winner);
      }
    };

    // Cleanup WebSocket when the component unmounts
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    // Check for a winner when scores update
    if (player1Score >= 16) setWinner(player1Name);
    else if (player2Score >= 16) setWinner(player2Name);
  }, [player1Score, player2Score, player1Name, player2Name]);

  const resetGame = () => {
    setIsResetting(true);
    setWinner(null);

    // Send 'reset' command to the WebSocket server
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ command: 'reset' }));
    }

    const resetInterval = setInterval(() => {
      setPlayer1Score((prev) => Math.max(0, prev - 1));
      setPlayer2Score((prev) => Math.max(0, prev - 1));
    }, 50);

    setTimeout(() => {
      clearInterval(resetInterval);
      setIsResetting(false);
    }, 1000);
  };

  const getScoreColor = (score) => {
    if (score < 6) return 'progress-low';
    if (score < 11) return 'progress-medium';
    return 'progress-high';
  };

  return (
    <div className="game-background">
      <div className="background-overlay" />
      <div className="content-container">
        <h1 className="game-title">Battleship Game</h1>

        {winner && (
          <div className="winner-banner">
            <div className="winner-text">{winner} Wins! 🎉</div>
          </div>
        )}

        <div className="game-card">
          <div className="players-container">
            {[{ name: player1Name, score: player1Score, colorClass: 'player-one' },
              { name: player2Name, score: player2Score, colorClass: 'player-two' }]
              .map((player, index) => (
                <div key={index} className="player-stats">
                  <div className="player-header">
                    <h2 className={`player-name ${player.colorClass}`}>{player.name}</h2>
                    <span className="score-text">{player.score}/16 Ships</span>
                  </div>
                  <div className="progress-bar-container">
                    <div
                      className={`progress-bar ${getScoreColor(player.score)}`}
                      style={{ width: `${(player.score / 16) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>

          <button
            onClick={resetGame}
            disabled={isResetting}
            className={`reset-button ${isResetting ? 'resetting' : ''}`}
          >
            <svg
              className={`reset-icon ${isResetting ? 'spinning' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {isResetting ? 'Resetting...' : 'Reset Game'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BattleshipGame;
