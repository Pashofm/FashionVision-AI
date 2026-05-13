import React, { useEffect, useRef } from 'react';
import '../styles/live-bbox-overlay.css';

const LiveBboxOverlay = ({ videoRef, detections, activeIndices = [] }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !videoRef?.current) return;

    const video = videoRef.current;
    let animationFrameId;

    const draw = () => {
      if (!video.videoWidth || !video.videoHeight) {
        animationFrameId = requestAnimationFrame(draw);
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (detections && detections.length > 0) {
        detections.forEach((det, index) => {
          const [x1, y1, x2, y2] = det.bbox || [0, 0, 0, 0];
          const isActive = activeIndices.includes(index);

          ctx.strokeStyle = isActive ? '#00ff88' : '#00ff00';
          ctx.lineWidth = isActive ? 3 : 2;

          const width = x2 - x1;
          const height = y2 - y1;

          ctx.strokeRect(x1, y1, width, height);

          const label = `${det.class?.toUpperCase() || 'ITEM'} ${Math.round((det.confidence || 0) * 100)}%`;

          ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
          ctx.font = 'bold 12px sans-serif';
          const textMetrics = ctx.measureText(label);
          ctx.fillRect(x1, y1 - 20, textMetrics.width + 10, 18);

          ctx.fillStyle = isActive ? '#00ff88' : '#00ff00';
          ctx.fillText(label, x1 + 5, y1 - 6);
        });
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [videoRef, detections, activeIndices]);

  return (
    <canvas
      ref={canvasRef}
      className="live-bbox-canvas"
    />
  );
};

export default LiveBboxOverlay;