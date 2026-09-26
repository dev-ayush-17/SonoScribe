import React, { useState } from 'react';
import { Search, Calendar, Clock, FileText, Trash2 } from 'lucide-react';
import type { Meeting } from '../types';

interface Props {
  meetings: Meeting[];
  selectedMeetingId?: string;
  onSelectMeeting: (id: string) => void;
  onDeleteMeeting: (id: string) => void;
}

export const MeetingList: React.FC<Props> = ({
  meetings,
  selectedMeetingId,
  onSelectMeeting,
  onDeleteMeeting,
}) => {
  const [search, setSearch] = useState('');

  const filteredMeetings = meetings.filter((m) =>
    m.title.toLowerCase().includes(search.toLowerCase())
  );

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: '12px',
      padding: '20px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Past Meetings ({meetings.length})
        </h2>
      </div>

      {/* Search Bar */}
      <div style={{ position: 'relative', marginBottom: '16px' }}>
        <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
        <input
          type="text"
          placeholder="Search meetings by title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: '32px' }}
        />
      </div>

      {/* List */}
      <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {filteredMeetings.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No recorded meetings found. Start a recording above to capture transcript segments.
          </div>
        ) : (
          filteredMeetings.map((meeting) => {
            const isSelected = meeting.id === selectedMeetingId;
            return (
              <div
                key={meeting.id}
                onClick={() => onSelectMeeting(meeting.id)}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: `1px solid ${isSelected ? 'var(--accent-blue)' : 'var(--border-subtle)'}`,
                  background: isSelected ? 'rgba(59, 130, 246, 0.08)' : 'var(--bg-input)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', paddingRight: '20px' }}>
                    {meeting.title}
                  </h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete meeting "${meeting.title}"?`)) {
                        onDeleteMeeting(meeting.id);
                      }
                    }}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      padding: '4px',
                      color: 'var(--text-muted)',
                    }}
                    title="Delete meeting"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={12} /> {formatDate(meeting.started_at)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)' }}>
                    <Clock size={12} /> {formatDuration(meeting.duration_seconds)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <FileText size={12} /> {meeting.segment_count} seg
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
