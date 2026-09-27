import React, { useState } from 'react';
import { Search, Calendar, Clock, FileText, Trash2, FolderOpen } from 'lucide-react';
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
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      padding: '20px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FolderOpen size={16} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Past Meetings
          </h2>
        </div>
        <span style={{
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
          background: 'var(--bg-input)',
          padding: '3px 10px',
          borderRadius: '9999px',
          color: 'var(--text-muted)',
          border: '1px solid var(--border-subtle)',
          fontWeight: 600,
        }}>
          {meetings.length} total
        </span>
      </div>

      {/* Search Bar */}
      <div style={{ position: 'relative' }}>
        <Search size={13} style={{
          position: 'absolute',
          left: '11px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: 'var(--text-muted)',
        }} />
        <input
          type="text"
          placeholder="Search by title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: '32px', fontSize: '0.82rem' }}
        />
      </div>

      {/* List */}
      <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {filteredMeetings.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '36px 16px',
            color: 'var(--text-muted)',
            fontSize: '0.82rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
          }}>
            <FileText size={28} style={{ opacity: 0.3 }} />
            <span>{search ? 'No meetings match your search.' : 'No recordings yet. Start one above!'}</span>
          </div>
        ) : (
          filteredMeetings.map((meeting) => {
            const isSelected = meeting.id === selectedMeetingId;
            return (
              <div
                key={meeting.id}
                className={`meeting-item ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectMeeting(meeting.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <h3 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)',
                    paddingRight: '20px',
                    lineHeight: 1.3,
                    transition: 'color 0.15s ease',
                  }}>
                    {meeting.title}
                  </h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete "${meeting.title}"? This cannot be undone.`)) {
                        onDeleteMeeting(meeting.id);
                      }
                    }}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      padding: '4px',
                      color: 'var(--text-muted)',
                      opacity: 0.6,
                      flexShrink: 0,
                    }}
                    title="Delete meeting"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  flexWrap: 'wrap',
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={11} /> {formatDate(meeting.started_at)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)' }}>
                    <Clock size={11} /> {formatDuration(meeting.duration_seconds)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <FileText size={11} /> {meeting.segment_count} seg
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
