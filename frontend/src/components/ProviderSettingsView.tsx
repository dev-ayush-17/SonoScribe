import React from 'react';
import { Cpu, Sparkles, CheckCircle2, Server, RefreshCw } from 'lucide-react';
import type { AppConfig } from '../types';

interface Props {
  config?: AppConfig;
  onRefresh: () => void;
}

export const ProviderSettingsView: React.FC<Props> = ({ config, onRefresh }) => {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: '16px',
      padding: '28px',
      boxShadow: 'var(--shadow-md)',
      minHeight: '520px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server color="var(--accent-cyan)" size={22} /> Provider & Engine Configuration
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Manage local STT models and AI providers configured in backend/.env
          </p>
        </div>

        <button onClick={onRefresh}>
          <RefreshCw size={14} /> Refresh Status
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* STT Engine Card */}
        <div style={{
          background: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '20px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Cpu size={20} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Speech-to-Text Engine
              </h3>
            </div>
            <span className="badge badge-completed">
              <CheckCircle2 size={12} color="var(--accent-green)" /> Ready
            </span>
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div><strong>Active Provider:</strong> {config?.transcription.name || 'faster-whisper'}</div>
            <div><strong>Whisper Model:</strong> base.en (int8 CPU)</div>
            <div><strong>Sample Rate:</strong> {config?.audio_sample_rate || 16000} Hz</div>
            <div><strong>Storage Mode:</strong> SQLite Timestamped Segments</div>
          </div>
        </div>

        {/* AI LLM Provider Card */}
        <div style={{
          background: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '20px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sparkles size={20} color="var(--accent-amber)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                AI Notes Provider
              </h3>
            </div>
            <span className="badge badge-completed">
              <CheckCircle2 size={12} color="var(--accent-green)" /> Configured
            </span>
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div><strong>Active Provider:</strong> {config?.ai.name || 'huggingface'}</div>
            <div><strong>Supported Providers:</strong> Hugging Face, Groq, Ollama, Gemini</div>
            <div><strong>Window Processing:</strong> 20-25 Minute Sliding Blocks</div>
            <div><strong>Config Location:</strong> <code>backend/.env</code></div>
          </div>
        </div>
      </div>
    </div>
  );
};
