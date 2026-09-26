import React, { useState } from 'react';
import { Sparkles, CheckSquare, HelpCircle, ListCheck, Clock, RefreshCw, AlertCircle } from 'lucide-react';
import type { AiNote } from '../types';

interface Props {
  notes: AiNote[];
  onGenerateNotes: () => Promise<void>;
}

export const AiNotesView: React.FC<Props> = ({ notes, onGenerateNotes }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const latestNote = notes.length > 0 ? notes[0] : null;

  const handleGenerate = async () => {
    setIsGenerating(true);
    setErrorMsg(null);
    try {
      await onGenerateNotes();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate AI notes');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header action */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            AI Meeting Notes & Summary
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Structured synthesis: facts, decisions, action items, and open questions
          </p>
        </div>

        <button
          className="primary"
          onClick={handleGenerate}
          disabled={isGenerating}
        >
          <Sparkles size={16} />
          {isGenerating ? 'Generating Notes...' : latestNote ? 'Regenerate Notes' : 'Generate AI Notes'}
        </button>
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
          fontSize: '0.85rem',
        }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {!latestNote && !isGenerating && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          background: 'var(--bg-input)',
          border: '1px border-dashed var(--border-subtle)',
          borderRadius: '8px',
          color: 'var(--text-muted)',
        }}>
          <Sparkles size={32} style={{ margin: '0 auto 12px', opacity: 0.5, color: 'var(--accent-yellow)' }} />
          <p style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '4px' }}>
            No AI Notes Generated Yet
          </p>
          <p style={{ fontSize: '0.8rem', maxWidth: '400px', margin: '0 auto 16px' }}>
            Click "Generate AI Notes" above to process the transcript using your configured local (Ollama) or cloud (Groq/Gemini) provider.
          </p>
        </div>
      )}

      {isGenerating && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          background: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          color: 'var(--text-muted)',
        }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 12px', color: 'var(--accent-blue)' }} />
          <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Analyzing transcript segments & synthesizing notes...</p>
        </div>
      )}

      {latestNote && latestNote.status === 'completed' && !isGenerating && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Executive Summary */}
          {latestNote.summary && (
            <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Summary
              </h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                {latestNote.summary}
              </p>
            </div>
          )}

          {/* Decisions */}
          {latestNote.decisions && latestNote.decisions.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-green)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                <CheckSquare size={16} /> Explicit Decisions Made
              </h4>
              <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.875rem' }}>
                {latestNote.decisions.map((decision, idx) => (
                  <li key={idx} style={{ color: 'var(--text-primary)' }}>{decision}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {latestNote.action_items && latestNote.action_items.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-yellow)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                <ListCheck size={16} /> Action Items
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {latestNote.action_items.map((item, idx) => (
                  <div key={idx} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.875rem',
                  }}>
                    <span style={{ color: 'var(--text-primary)' }}>• {item.task}</span>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span><strong>Owner:</strong> {item.owner}</span>
                      <span><strong>Due:</strong> {item.due_date}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Open Questions */}
          {latestNote.open_questions && latestNote.open_questions.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                <HelpCircle size={16} /> Open Questions & Assumptions
              </h4>
              <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.875rem' }}>
                {latestNote.open_questions.map((q, idx) => (
                  <li key={idx} style={{ color: 'var(--text-secondary)' }}>{q}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Notable Timestamps */}
          {latestNote.notable_timestamps && latestNote.notable_timestamps.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                <Clock size={16} /> Notable Timestamps
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.85rem' }}>
                {latestNote.notable_timestamps.map((ts, idx) => (
                  <div key={idx} style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                    {ts}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
