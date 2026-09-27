import React from 'react';

interface Props {
  isRecording: boolean;
}

export const AudioVisualizer: React.FC<Props> = ({ isRecording }) => {
  const bars = [14, 28, 18, 36, 22, 42, 16, 32, 24, 38, 12, 26, 30, 20, 34];

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      height: '36px',
      padding: '0 12px',
      background: 'var(--bg-input)',
      borderRadius: '8px',
      border: '1px solid var(--border-subtle)',
    }}>
      {bars.map((h, i) => (
        <div
          key={i}
          className={isRecording ? 'waveform-bar' : ''}
          style={{
            width: '3px',
            height: isRecording ? `${h}px` : '4px',
            background: isRecording ? 'var(--accent-cyan)' : 'var(--text-muted)',
            borderRadius: '2px',
            animationDelay: `${(i % 5) * 0.15}s`,
            transition: 'all 0.3s ease',
          }}
        />
      ))}
    </div>
  );
};
