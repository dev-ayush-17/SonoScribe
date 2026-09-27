import React, { useState, useEffect } from 'react';
import { Play, Square, Clock, AlertCircle, Radio, Volume2, Sparkles, Sliders } from 'lucide-react';
import type { AudioDevice, RecordingStatus, TranscriptSegment } from '../types';
import { ConsentModal } from './ConsentModal';
import { AudioVisualizer } from './AudioVisualizer';

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

  const recentSegments = liveSegments.slice(-5);

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
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      marginBottom: '24px',
      boxShadow: 'var(--shadow-md)',
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color var(--transition-base)',
    }}>
      {/* Studio Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {recordingStatus.is_recording ? (
            <div className="badge badge-recording" style={{ padding: '6px 12px' }}>
              <span className="pulse-dot"></span>
              <span style={{ fontWeight: 600 }}>STUDIO LIVE RECORDING</span>
            </div>
          ) : (
            <div className="badge badge-idle" style={{ padding: '6px 12px' }}>
              <Radio size={14} color="var(--text-muted)" />
              <span>Studio Idle</span>
            </div>
          )}

          {/* Live Waveform Visualizer */}
          <AudioVisualizer isRecording={recordingStatus.is_recording} />

          {recordingStatus.is_recording && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontFamily: 'var(--font-mono)',
              fontSize: '1.1rem',
              fontWeight: 600,
              color: 'var(--accent-red)',
              background: 'rgba(244, 63, 94, 0.1)',
              padding: '4px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(244, 63, 94, 0.3)',
            }}>
              <Clock size={16} color="var(--accent-red)" />
              {formatElapsed(elapsed)}
            </div>
          )}
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} color="var(--accent-teal)" />
          {recordingStatus.segment_count > 0 ? (
            <span><strong>{recordingStatus.segment_count}</strong> chunks processed & saved</span>
          ) : (
            <span>WASAPI System Loopback + Mic Audio</span>
          )}
        </div>
      </div>

      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.35)',
          color: 'var(--accent-red)',
          padding: '12px 16px',
          borderRadius: '10px',
          marginBottom: '20px',
          fontSize: '0.875rem',
        }}>
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Control Grid Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr auto', gap: '16px', alignItems: 'center' }}>
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
            MEETING TITLE
          </label>
          <input
            type="text"
            placeholder="e.g. Sprint Planning, Client Sync, Design Review..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={recordingStatus.is_recording || isSubmitting}
          />
        </div>

        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
            <Sliders size={12} /> AUDIO SOURCE DEVICE
          </label>
          <select
            value={selectedDevice}
            onChange={(e) => setSelectedDevice(e.target.value)}
            disabled={recordingStatus.is_recording || isSubmitting}
          >
            {devices.map((dev) => (
              <option key={`${dev.index}-${dev.name}`} value={dev.name}>
                {dev.is_loopback ? '🔊 System Audio Output' : '🎤 Microphone Input'} — {dev.name}
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
              style={{ height: '42px', padding: '0 24px', fontSize: '0.9rem' }}
            >
              <Play size={18} fill="currentColor" /> Start Recording
            </button>
          ) : (
            <button
              className="danger"
              onClick={handleStopClick}
              disabled={isSubmitting}
              style={{ height: '42px', padding: '0 24px', fontSize: '0.9rem' }}
            >
              <Square size={18} fill="currentColor" /> Finish Recording
            </button>
          )}
        </div>
      </div>

      {/* Live Stream Panel */}
      {recordingStatus.is_recording && (
        <div style={{ marginTop: '24px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--accent-cyan)' }}>
              LIVE STREAMING TRANSCRIPT
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              WebSocket Real-time Feed
            </span>
          </div>

          <div style={{
            background: 'var(--bg-main)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            maxHeight: '220px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            {recentSegments.length === 0 ? (
              <div style={{
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                padding: '24px 0',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
              }}>
                <Volume2 size={22} style={{ opacity: 0.4, color: 'var(--accent-cyan)' }} />
                <span>Listening... chunks process every 1-minute window</span>
              </div>
            ) : (
              recentSegments.map((seg, idx) => (
                <div key={idx} className="segment-card">
                  <span className="segment-timestamp">
                    {Math.floor(seg.start_time / 60)}:{(Math.floor(seg.start_time % 60)).toString().padStart(2, '0')}
                  </span>
                  <span style={{ color: 'var(--text-primary)', lineHeight: 1.55, fontSize: '0.875rem' }}>{seg.text}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Consent Confirmation Modal */}
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
