import React, { useState, useEffect } from 'react';
import { Play, Square, Volume2, Clock, AlertCircle, FileCheck } from 'lucide-react';
import type { AudioDevice, RecordingStatus, TranscriptSegment } from '../types';
import { ConsentModal } from './ConsentModal';

interface Props {
  devices: AudioDevice[];
  recordingStatus: RecordingStatus;
  liveSegments: TranscriptSegment[];
  onStartRecording: (title: string, device?: string) => Promise<void>;
  onStopRecording: () => Promise<void>;
}

export const RecordingControl: React.FC<Props> = ({
  devices,
  recordingStatus,
  liveSegments,
  onStartRecording,
  onStopRecording,
}) => {
  const [title, setTitle] = useState('');
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  // Cap live streaming display to recent 6 segments
  const recentSegments = liveSegments.slice(-6);

  useEffect(() => {
    if (devices.length > 0 && !selectedDevice) {
      const defaultLoopback = devices.find((d) => d.is_loopback);
      if (defaultLoopback) {
        setSelectedDevice(defaultLoopback.name);
      } else {
        setSelectedDevice(devices[0].name);
      }
    }
  }, [devices, selectedDevice]);

  useEffect(() => {
    let interval: any;
    if (recordingStatus.is_recording) {
      interval = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsed(0);
    }
    return () => clearInterval(interval);
  }, [recordingStatus.is_recording]);

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartClick = () => {
    if (!title.trim()) {
      setTitle(`Meeting ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
    }
    setErrorMsg(null);
    setShowConsentModal(true);
  };

  const handleConfirmStart = async () => {
    setShowConsentModal(false);
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const meetingTitle = title.trim() || `Meeting ${new Date().toLocaleDateString()}`;
      await onStartRecording(meetingTitle, selectedDevice);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to start recording');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStopClick = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      await onStopRecording();
      setTitle('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to stop recording');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: '12px',
      padding: '24px',
      marginBottom: '24px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {recordingStatus.is_recording ? (
            <div className="badge badge-recording">
              <span className="pulse-dot"></span>
              Recording Live (1-Min Chunks)
            </div>
          ) : (
            <div className="badge badge-idle">
              <span>Idle</span>
            </div>
          )}
          {recordingStatus.is_recording && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
              <Clock size={16} color="var(--accent-red)" />
              {formatElapsed(elapsed)}
            </div>
          )}
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {recordingStatus.segment_count > 0 && `${recordingStatus.segment_count} 1-min segments written to session doc`}
        </div>
      </div>

      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: 'var(--accent-red)',
          padding: '10px 14px',
          borderRadius: '6px',
          marginBottom: '16px',
          fontSize: '0.85rem',
        }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Recording Form Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr auto', gap: '12px', alignItems: 'center' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
            MEETING TITLE
          </label>
          <input
            type="text"
            placeholder="e.g. Architecture Sync, Weekly Standup..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={recordingStatus.is_recording || isSubmitting}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
            AUDIO SOURCE
          </label>
          <select
            value={selectedDevice}
            onChange={(e) => setSelectedDevice(e.target.value)}
            disabled={recordingStatus.is_recording || isSubmitting}
          >
            {devices.map((dev) => (
              <option key={`${dev.index}-${dev.name}`} value={dev.name}>
                {dev.is_loopback ? '🔊 System Output (Loopback)' : '🎤 Input'} — {dev.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ alignSelf: 'end' }}>
          {!recordingStatus.is_recording ? (
            <button
              className="primary"
              onClick={handleStartClick}
              disabled={isSubmitting}
              style={{ height: '38px', padding: '0 20px' }}
            >
              <Play size={16} fill="currentColor" /> Start Recording
            </button>
          ) : (
            <button
              className="danger"
              onClick={handleStopClick}
              disabled={isSubmitting}
              style={{ height: '38px', padding: '0 20px' }}
            >
              <Square size={16} fill="currentColor" /> Stop Recording
            </button>
          )}
        </div>
      </div>

      {/* Live Streaming Transcript Panel capped to recent 6 transcripts */}
      {recordingStatus.is_recording && (
        <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
              LIVE RECENT TRANSCRIPTS (SHOWING RECENT {recentSegments.length} OF {liveSegments.length})
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <FileCheck size={14} /> Full Session Doc Auto-Updating
            </span>
          </div>

          <div style={{
            background: 'var(--bg-main)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '16px',
            maxHeight: '220px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}>
            {recentSegments.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '24px 0' }}>
                <Volume2 size={20} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                Listening for audio... Speech segments will appear live as 1-minute chunks process.
              </div>
            ) : (
              recentSegments.map((seg, idx) => (
                <div key={idx} style={{ display: 'flex', gap: '12px', fontSize: '0.875rem' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', minWidth: '48px' }}>
                    {Math.floor(seg.start_time / 60)}:{(Math.floor(seg.start_time % 60)).toString().padStart(2, '0')}
                  </span>
                  <span style={{ color: 'var(--text-primary)' }}>{seg.text}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Consent Modal */}
      <ConsentModal
        isOpen={showConsentModal}
        meetingTitle={title || 'Untitled Meeting'}
        deviceName={selectedDevice}
        onConfirm={handleConfirmStart}
        onCancel={() => setShowConsentModal(false)}
      />
    </div>
  );
};
