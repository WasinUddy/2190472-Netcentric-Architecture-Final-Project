import React from 'react';
import './Leaderboard.css';

const LeaderBoard = ({ winnerHistory }) => {
  // Ensure winnerHistory is an array before proceeding
  if (!Array.isArray(winnerHistory)) {
    console.error('Invalid winnerHistory prop. Expected an array.');
    return null; // Or return a fallback UI if needed
  }

  // Handle case when winnerHistory is empty
  if (winnerHistory.length === 0) {
    return (
      <div className="leaderboard">
        <h2 className="leaderboard-title">Leaderboard</h2>
        <p>No winners yet!</p>
      </div>
    );
  }

  // Count occurrences of each winner
  const countNames = winnerHistory.reduce((acc, name) => {
    acc[name] = (acc[name] || 0) + 1;
    return acc;
  }, {});

  // Sort leaderboard by win count
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

export default LeaderBoard;
