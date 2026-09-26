import { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { RecordingControl } from './components/RecordingControl';
import { MeetingList } from './components/MeetingList';
import { MeetingDetail } from './components/MeetingDetail';
import type {
  AppConfig,
  AudioDevice,
  HealthStatus,
  Meeting,
  MeetingDetail as IMeetingDetail,
  RecordingStatus,
  TranscriptSegment,
} from './types';
import {
  createTranscriptWebSocket,
  deleteMeeting,
  fetchAudioDevices,
  fetchConfig,
  fetchHealth,
  fetchMeetingDetail,
  fetchMeetings,
  fetchRecordingStatus,
  generateAiNotes,
  startRecording,
  stopRecording,
} from './services/api';

export function App() {
  const [health, setHealth] = useState<HealthStatus | undefined>();
  const [config, setConfig] = useState<AppConfig | undefined>();
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [recordingStatus, setRecordingStatus] = useState<RecordingStatus>({
    is_recording: false,
    status: 'idle',
    duration_seconds: 0,
    segment_count: 0,
  });
  const [liveSegments, setLiveSegments] = useState<TranscriptSegment[]>([]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | undefined>();
  const [selectedMeetingDetail, setSelectedMeetingDetail] = useState<IMeetingDetail | undefined>();

  const loadMetadata = useCallback(async () => {
    try {
      const [h, c, d, s] = await Promise.all([
        fetchHealth().catch(() => undefined),
        fetchConfig().catch(() => undefined),
        fetchAudioDevices().catch(() => []),
        fetchRecordingStatus().catch(() => ({
          is_recording: false,
          status: 'idle' as const,
          duration_seconds: 0,
          segment_count: 0,
        })),
      ]);
      setHealth(h);
      setConfig(c);
      setDevices(d);
      setRecordingStatus(s);
    } catch (e) {
      console.error('Failed to load system metadata:', e);
    }
  }, []);

  const loadMeetings = useCallback(async () => {
    try {
      const list = await fetchMeetings();
      setMeetings(list);
      if (list.length > 0 && !selectedMeetingId) {
        setSelectedMeetingId(list[0].id);
      }
    } catch (e) {
      console.error('Failed to fetch meetings:', e);
    }
  }, [selectedMeetingId]);

  useEffect(() => {
    if (!selectedMeetingId) {
      setSelectedMeetingDetail(undefined);
      return;
    }
    fetchMeetingDetail(selectedMeetingId)
      .then(setSelectedMeetingDetail)
      .catch((err) => console.error('Failed to load meeting detail:', err));
  }, [selectedMeetingId]);

  useEffect(() => {
    loadMetadata();
    loadMeetings();
  }, [loadMetadata, loadMeetings]);

  useEffect(() => {
    const ws = createTranscriptWebSocket(
      (segmentData) => {
        setLiveSegments((prev) => [...prev, segmentData]);
        setRecordingStatus((prev) => ({
          ...prev,
          segment_count: prev.segment_count + 1,
        }));
      },
      (statusData) => {
        setRecordingStatus(statusData);
      }
    );

    return () => {
      ws.close();
    };
  }, []);

  const handleStartRecording = async (title: string, device?: string) => {
    setLiveSegments([]);
    const res = await startRecording(title, device);
    setRecordingStatus({
      is_recording: true,
      meeting_id: res.meeting_id,
      status: 'recording',
      duration_seconds: 0,
      segment_count: 0,
    });
  };

  const handleStopRecording = async () => {
    const res = await stopRecording();
    setRecordingStatus({
      is_recording: false,
      status: 'idle',
      duration_seconds: res.duration_seconds,
      segment_count: res.segment_count,
    });
    await loadMeetings();
    setSelectedMeetingId(res.meeting_id);
  };

  const handleDeleteMeeting = async (id: string) => {
    await deleteMeeting(id);
    if (selectedMeetingId === id) {
      setSelectedMeetingId(undefined);
    }
    loadMeetings();
  };

  const handleGenerateAiNotes = async () => {
    if (!selectedMeetingId) return;
    await generateAiNotes(selectedMeetingId);
    const updated = await fetchMeetingDetail(selectedMeetingId);
    setSelectedMeetingDetail(updated);
  };

  return (
    <div className="app-container">
      <Header health={health} config={config} onRefreshConfig={loadMetadata} />

      <RecordingControl
        devices={devices}
        recordingStatus={recordingStatus}
        liveSegments={liveSegments}
        onStartRecording={handleStartRecording}
        onStopRecording={handleStopRecording}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', minHeight: '520px' }}>
        <MeetingList
          meetings={meetings}
          selectedMeetingId={selectedMeetingId}
          onSelectMeeting={setSelectedMeetingId}
          onDeleteMeeting={handleDeleteMeeting}
        />

        <div>
          {selectedMeetingDetail ? (
            <MeetingDetail
              meeting={selectedMeetingDetail}
              onGenerateAiNotes={handleGenerateAiNotes}
            />
          ) : (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '40px',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              textAlign: 'center',
            }}>
              <div>
                <p style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  No Meeting Selected
                </p>
                <p style={{ fontSize: '0.85rem' }}>Select a past meeting from the left list or start a new recording.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
