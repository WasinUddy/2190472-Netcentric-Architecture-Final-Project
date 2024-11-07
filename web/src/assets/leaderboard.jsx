import React from 'react';
import './leaderboard.css';

const Leaderboard = ({ winnerHistory }) => {
  const countNames = winnerHistory.reduce((acc, name) => {
    acc[name] = (acc[name] || 0) + 1;
    return acc;
  }, {});

  const leaderboard = Object.entries(countNames)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="leaderboard">
      <h2 className="leaderboard-title">Leaderboard</h2>
      <div className="leaderboard-list">
        {leaderboard.map((player, index) => (
          <div key={index} className="leaderboard-item">
            <span>{player.name}</span>
            <span>{player.count} wins</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Leaderboard;
