import React from 'react';
import { Cpu, Sparkles, Database, CheckCircle2, XCircle, Search, ShieldCheck, Wifi, WifiOff } from 'lucide-react';
import type { AppConfig, HealthStatus } from '../types';

interface Props {
  health?: HealthStatus;
  config?: AppConfig;
  onRefreshConfig?: () => void;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
}

export const Header: React.FC<Props> = ({ config, health, searchQuery, onSearchChange }) => {
  const isOnline = health !== undefined;

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingBottom: '24px',
      borderBottom: '1px solid var(--border-subtle)',
      marginBottom: '28px',
      gap: '20px',
    }}>
      {/* Search Bar */}
      <div style={{ position: 'relative', flex: '0 1 420px' }}>
        <Search size={15} style={{
          position: 'absolute',
          left: '12px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: 'var(--text-muted)',
        }} />
        <input
          type="text"
          placeholder="Search transcripts, decisions, action items..."
          value={searchQuery || ''}
          onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
          style={{
            paddingLeft: '38px',
            paddingRight: '56px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
          }}
        />
        <span style={{
          position: 'absolute',
          right: '10px',
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: '0.68rem',
          fontFamily: 'var(--font-mono)',
          background: 'var(--bg-accent)',
          padding: '2px 7px',
          borderRadius: '4px',
          color: 'var(--text-muted)',
          border: '1px solid var(--border-subtle)',
          letterSpacing: '0.02em',
        }}>
          ⌘K
        </span>
      </div>

      {/* Status Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        {/* Backend connectivity */}
        <div className="badge" title={isOnline ? 'Backend connected' : 'Backend offline'}>
          {isOnline ? (
            <Wifi size={13} color="var(--accent-teal)" />
          ) : (
            <WifiOff size={13} color="var(--accent-red)" />
          )}
          <span style={{ color: isOnline ? 'var(--accent-teal)' : 'var(--text-muted)', fontWeight: 600, fontSize: '0.72rem' }}>
            {isOnline ? 'Connected' : 'Offline'}
          </span>
        </div>

        {/* Transcription Engine */}
        <div className="badge" title="Transcription Engine">
          <Cpu size={13} color="var(--accent-cyan)" />
          <span style={{ textTransform: 'capitalize', color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.72rem' }}>
            {config?.transcription.name || 'Whisper'}
          </span>
          {config?.transcription.available ? (
            <CheckCircle2 size={12} color="var(--accent-green)" />
          ) : (
            <XCircle size={12} color="var(--accent-red)" />
          )}
        </div>

        {/* AI Notes Engine */}
        <div className="badge" title="AI Provider">
          <Sparkles size={13} color="var(--accent-amber)" />
          <span style={{ fontSize: '0.72rem' }}>
            AI:{' '}
            <strong style={{ color: 'var(--text-primary)' }}>
              {config?.ai.name && config.ai.name !== 'none' ? config.ai.name : 'Off'}
            </strong>
          </span>
          {config?.ai.available ? (
            <CheckCircle2 size={12} color="var(--accent-green)" />
          ) : (
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>(opt-in)</span>
          )}
        </div>

        {/* Storage */}
        <div className="badge" title="Local SQLite Storage">
          <Database size={13} color="var(--accent-teal)" />
          <span style={{ fontSize: '0.72rem' }}>SQLite</span>
          <ShieldCheck size={12} color="var(--accent-green)" />
        </div>
      </div>
    </header>
  );
};
