import React, { useState } from 'react';
import { Sparkles, ListCheck, RefreshCw, AlertCircle, FileText, Calendar, Lightbulb } from 'lucide-react';
import type { AiNote } from '../types';

interface Props {
  notes: AiNote[];
  artifacts?: Record<string, string>;
  onGenerateNotes: () => Promise<void>;
}

export const AiNotesView: React.FC<Props> = ({ notes, artifacts, onGenerateNotes }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedDocTab, setSelectedDocTab] = useState<string>('minutes');

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

  const minutesDoc = artifacts?.minutes_of_meeting || latestNote?.summary || '';
  const highlightsDoc = artifacts?.highlights || '';
  const actionItemsDoc = artifacts?.action_items || '';
  const proposalsDoc = artifacts?.proposals_and_future_plans || '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header action */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            AI Windowed Meeting Artifacts (20-25 Min Blocks)
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Synthesized documents: Minutes of Meeting, Highlights, Action Items, Proposals & Schedules
          </p>
        </div>

        <button
          className="primary"
          onClick={handleGenerate}
          disabled={isGenerating}
        >
          <Sparkles size={16} />
          {isGenerating ? 'Synthesizing 20m Windows...' : (latestNote || artifacts) ? 'Regenerate Meeting Artifacts' : 'Generate AI Artifacts'}
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

      {/* Sub-document tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        <button
          onClick={() => setSelectedDocTab('minutes')}
          style={{
            background: selectedDocTab === 'minutes' ? 'var(--bg-accent)' : 'transparent',
            borderColor: selectedDocTab === 'minutes' ? 'var(--border-focus)' : 'transparent',
            fontSize: '0.8rem',
          }}
        >
          <FileText size={14} /> Minutes of Meeting
        </button>
        <button
          onClick={() => setSelectedDocTab('highlights')}
          style={{
            background: selectedDocTab === 'highlights' ? 'var(--bg-accent)' : 'transparent',
            borderColor: selectedDocTab === 'highlights' ? 'var(--border-focus)' : 'transparent',
            fontSize: '0.8rem',
          }}
        >
          <Lightbulb size={14} color="var(--accent-yellow)" /> Highlights
        </button>
        <button
          onClick={() => setSelectedDocTab('actions')}
          style={{
            background: selectedDocTab === 'actions' ? 'var(--bg-accent)' : 'transparent',
            borderColor: selectedDocTab === 'actions' ? 'var(--border-focus)' : 'transparent',
            fontSize: '0.8rem',
          }}
        >
          <ListCheck size={14} color="var(--accent-green)" /> Action Items & Schedules
        </button>
        <button
          onClick={() => setSelectedDocTab('proposals')}
          style={{
            background: selectedDocTab === 'proposals' ? 'var(--bg-accent)' : 'transparent',
            borderColor: selectedDocTab === 'proposals' ? 'var(--border-focus)' : 'transparent',
            fontSize: '0.8rem',
          }}
        >
          <Calendar size={14} color="var(--accent-blue)" /> Proposals & Future Plans
        </button>
      </div>

      {!latestNote && !artifacts && !isGenerating && (
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
            No AI Meeting Artifacts Generated Yet
          </p>
          <p style={{ fontSize: '0.8rem', maxWidth: '440px', margin: '0 auto 16px' }}>
            Click "Generate AI Artifacts" above to process transcript windows (20-25m blocks) using Groq / Ollama / Gemini.
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
          <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Processing transcript in 20-25 minute windowed blocks & extracting artifacts...</p>
        </div>
      )}

      {/* Render Document Content */}
      {!isGenerating && (
        <div style={{ background: 'var(--bg-input)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          {selectedDocTab === 'minutes' && (
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '0.9rem' }}>
              {minutesDoc || 'No minutes of meeting document generated yet.'}
            </div>
          )}

          {selectedDocTab === 'highlights' && (
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '0.9rem' }}>
              {highlightsDoc || 'No highlights document generated yet.'}
            </div>
          )}

          {selectedDocTab === 'actions' && (
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '0.9rem' }}>
              {actionItemsDoc || (
                latestNote?.action_items && latestNote.action_items.length > 0 ? (
                  <div>
                    <h4 style={{ marginBottom: '12px' }}>Action Items</h4>
                    {latestNote.action_items.map((item, idx) => (
                      <div key={idx} style={{ padding: '8px', marginBottom: '6px', background: 'var(--bg-card)', borderRadius: '6px' }}>
                        • {item.task} (Owner: {item.owner}, Due: {item.due_date})
                      </div>
                    ))}
                  </div>
                ) : 'No action items document generated yet.'
              )}
            </div>
          )}

          {selectedDocTab === 'proposals' && (
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '0.9rem' }}>
              {proposalsDoc || 'No proposals & future plans document generated yet.'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
