import React from 'react';
import '../styles/countdown-overlay.css';

const CountdownOverlay = ({ countdown, message, onCancel }) => {
  if (countdown === null) return null;

  return (
    <div className="mini-countdown-overlay">
      <div className="countdown-mini-banner">
        <span className="countdown-message">{message}</span>
        <span className="countdown-number">{countdown}</span>
        {onCancel && (
          <button className="countdown-cancel-btn" onClick={onCancel}>
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default CountdownOverlay;