import React from 'react';
import { Mic, Cpu, Sparkles, Database, CheckCircle2, XCircle } from 'lucide-react';
import type { AppConfig, HealthStatus } from '../types';

interface Props {
  health?: HealthStatus;
  config?: AppConfig;
  onRefreshConfig?: () => void;
}

export const Header: React.FC<Props> = ({ config }) => {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 0',
      borderBottom: '1px solid var(--border-subtle)',
      marginBottom: '24px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #27272a, #09090b)',
          border: '1px solid var(--border-focus)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-primary)',
        }}>
          <Mic size={20} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
            SonoScribe
          </h1>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Local-First Meeting Recorder & AI Transcriber
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Transcription Provider Pill */}
        <div className="badge" title="Transcription Engine">
          <Cpu size={14} color="var(--accent-blue)" />
          <span style={{ textTransform: 'capitalize' }}>
            {config?.transcription.name || 'faster-whisper'}
          </span>
          {config?.transcription.available ? (
            <CheckCircle2 size={12} color="var(--accent-green)" />
          ) : (
            <XCircle size={12} color="var(--accent-red)" />
          )}
        </div>

        {/* AI Provider Pill */}
        <div className="badge" title="AI Notes Engine">
          <Sparkles size={14} color="var(--accent-yellow)" />
          <span>
            AI: {config?.ai.name && config.ai.name !== 'none' ? config.ai.name : 'Off / Configurable'}
          </span>
          {config?.ai.available ? (
            <CheckCircle2 size={12} color="var(--accent-green)" />
          ) : (
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>(Opt-in)</span>
          )}
        </div>

        {/* Local DB Indicator */}
        <div className="badge" title="SQLite Database Status">
          <Database size={14} color="var(--text-secondary)" />
          <span>SQLite</span>
          <CheckCircle2 size={12} color="var(--accent-green)" />
        </div>
      </div>
    </header>
  );
};
