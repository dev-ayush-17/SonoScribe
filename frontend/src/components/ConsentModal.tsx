import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface Props {
  isOpen: boolean;
  meetingTitle: string;
  deviceName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConsentModal: React.FC<Props> = ({
  isOpen,
  meetingTitle,
  deviceName,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-yellow)' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Recording Consent</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confirm before proceeding</p>
          </div>
        </div>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          You are about to start recording audio for <strong>"{meetingTitle || 'Untitled Meeting'}"</strong> using audio device <em>{deviceName || 'Default Output Loopback'}</em>.
        </p>

        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '20px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '4px' }}>
            <ShieldCheck size={16} /> Privacy & Local Processing
          </div>
          Audio is captured locally in-memory, transcribed continuously, and stored directly in your local SQLite database. Ensure all meeting participants have consented to being recorded.
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button onClick={onCancel}>Cancel</button>
          <button className="primary" onClick={onConfirm}>
            I Confirm & Start Recording
          </button>
        </div>
      </div>
    </div>
  );
};
