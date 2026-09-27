import React, { useState } from 'react';
import { CheckSquare, Calendar, User, Sparkles } from 'lucide-react';
import type { Meeting } from '../types';

interface Props {
  meetings: Meeting[];
}

export const ActionItemsHub: React.FC<Props> = ({ meetings }) => {
  const [completedTasks, setCompletedTasks] = useState<Record<string, boolean>>({});

  const toggleTask = (key: string) => {
    setCompletedTasks((prev) => ({ ...prev, [key]: !prev[key] }));
  };

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
            <CheckSquare color="var(--accent-teal)" size={22} /> Action Items & Task Tracker
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Consolidated task extraction across all recorded meeting sessions
          </p>
        </div>
      </div>

      {meetings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          <Sparkles size={36} style={{ margin: '0 auto 12px', opacity: 0.5, color: 'var(--accent-teal)' }} />
          <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
            No Meetings Recorded Yet
          </p>
          <p style={{ fontSize: '0.85rem' }}>Record a meeting to generate AI action items, tasks, and deadlines.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {meetings.map((meeting) => (
            <div key={meeting.id} style={{
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '18px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {meeting.title}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {new Date(meeting.started_at).toLocaleDateString()}
                </span>
              </div>

              {/* Sample Action Items checklist */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {['Finalize architecture specification document', 'Setup local Whisper fallback logic'].map((taskText, idx) => {
                  const taskKey = `${meeting.id}-${idx}`;
                  const isDone = !!completedTasks[taskKey];
                  return (
                    <div
                      key={idx}
                      onClick={() => toggleTask(taskKey)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '10px 14px',
                        background: 'var(--bg-card)',
                        borderRadius: '8px',
                        border: '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        opacity: isDone ? 0.5 : 1,
                        textDecoration: isDone ? 'line-through' : 'none',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input
                          type="checkbox"
                          checked={isDone}
                          onChange={() => {}}
                          style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                        />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{taskText}</span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <User size={12} /> Unassigned
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={12} /> Friday
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
