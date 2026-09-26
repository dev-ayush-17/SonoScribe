import React, { useState, useEffect } from 'react';
import { Download, Sparkles, FileText, Calendar, Clock, Copy, Check, FileCheck } from 'lucide-react';
import type { MeetingDetail as IMeetingDetail } from '../types';
import { exportTranscript } from '../services/api';
import { AiNotesView } from './AiNotesView';

interface Props {
  meeting: IMeetingDetail;
  onGenerateAiNotes: () => Promise<void>;
}

export const MeetingDetail: React.FC<Props> = ({ meeting, onGenerateAiNotes }) => {
  const [activeTab, setActiveTab] = useState<'transcript' | 'raw_file' | 'ai'>('transcript');
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [artifacts, setArtifacts] = useState<Record<string, string>>({});
  const [rawFileText, setRawFileText] = useState<string>('');

  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/meetings/${meeting.id}/artifacts`)
      .then((res) => res.json())
      .then((data) => {
        if (data.artifacts) setArtifacts(data.artifacts);
        if (data.raw_transcript) setRawFileText(data.raw_transcript);
      })
      .catch((err) => console.error('Failed to load session artifacts:', err));
  }, [meeting.id]);

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleExport = async (format: 'markdown' | 'text' | 'json') => {
    setExporting(true);
    try {
      const data = await exportTranscript(meeting.id, format);
      const blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${meeting.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_transcript.${format === 'markdown' ? 'md' : format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export transcript');
    } finally {
      setExporting(false);
    }
  };

  const handleCopyTranscript = () => {
    const text = rawFileText || meeting.segments.map((s) => `[${formatTimestamp(s.start_time)}] ${s.text}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: '12px',
      padding: '24px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {meeting.title}
          </h2>

          {/* Export Actions */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={handleCopyTranscript} title="Copy plain transcript text">
              {copied ? <Check size={14} color="var(--accent-green)" /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button onClick={() => handleExport('markdown')} disabled={exporting}>
              <Download size={14} /> Export MD
            </button>
            <button onClick={() => handleExport('text')} disabled={exporting}>
              Export Text
            </button>
          </div>
        </div>

        {/* Metadata Bar */}
        <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Calendar size={13} /> {new Date(meeting.started_at).toLocaleDateString()} {new Date(meeting.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)' }}>
            <Clock size={13} /> {Math.floor((meeting.duration_seconds || 0) / 60)}m {Math.floor((meeting.duration_seconds || 0) % 60)}s
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <FileText size={13} /> {meeting.segments.length} 1-min segments
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('transcript')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'transcript' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            borderRadius: 0,
            color: activeTab === 'transcript' ? 'var(--text-primary)' : 'var(--text-muted)',
            paddingBottom: '8px',
          }}
        >
          <FileText size={16} /> Segment Timeline ({meeting.segments.length})
        </button>

        <button
          onClick={() => setActiveTab('raw_file')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'raw_file' ? '2px solid var(--accent-green)' : '2px solid transparent',
            borderRadius: 0,
            color: activeTab === 'raw_file' ? 'var(--text-primary)' : 'var(--text-muted)',
            paddingBottom: '8px',
          }}
        >
          <FileCheck size={16} color="var(--accent-green)" /> Session Transcript File
        </button>

        <button
          onClick={() => setActiveTab('ai')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'ai' ? '2px solid var(--accent-yellow)' : '2px solid transparent',
            borderRadius: 0,
            color: activeTab === 'ai' ? 'var(--text-primary)' : 'var(--text-muted)',
            paddingBottom: '8px',
          }}
        >
          <Sparkles size={16} color="var(--accent-yellow)" /> AI Artifacts & Minutes
        </button>
      </div>

      {/* Tab Contents */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {activeTab === 'transcript' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {meeting.segments.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                No transcript segments available for this meeting.
              </div>
            ) : (
              meeting.segments.map((seg) => (
                <div key={seg.id} style={{
                  display: 'flex',
                  gap: '16px',
                  padding: '12px',
                  borderRadius: '6px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    minWidth: '54px',
                    paddingTop: '2px',
                  }}>
                    [{formatTimestamp(seg.start_time)}]
                  </span>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {seg.text}
                    </p>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span>Engine: {seg.provider}</span>
                      {seg.model && <span>Model: {seg.model}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'raw_file' && (
          <div style={{
            background: 'var(--bg-main)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '16px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            color: 'var(--text-primary)',
          }}>
            {rawFileText || 'No raw session transcript document file found on disk for this meeting.'}
          </div>
        )}

        {activeTab === 'ai' && (
          <AiNotesView notes={meeting.ai_notes} artifacts={artifacts} onGenerateNotes={onGenerateAiNotes} />
        )}
      </div>
    </div>
  );
};
