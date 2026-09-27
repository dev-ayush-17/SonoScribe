import { useEffect, useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { RecordingControl } from './components/RecordingControl';
import { MeetingList } from './components/MeetingList';
import { MeetingDetail } from './components/MeetingDetail';
import { ActionItemsHub } from './components/ActionItemsHub';
import { ProviderSettingsView } from './components/ProviderSettingsView';
import { AnimatedBackground } from './components/AnimatedBackground';
import { Hero } from './components/Hero';
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
  const [activeTab, setActiveTab] = useState<'studio' | 'meetings' | 'actions' | 'settings'>('studio');
  const [showHero, setShowHero] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
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
    setShowHero(false);
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
    setActiveTab('meetings');
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

  const handleGetStarted = () => {
    setShowHero(false);
    setActiveTab('studio');
  };

  return (
    <>
      {/* Fixed animated background - sits behind everything */}
      <AnimatedBackground />

      <div className="app-shell">
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            setShowHero(false);
          }}
          meetingCount={meetings.length}
        />

        {/* Main Workspace Area */}
        <main className="main-workspace">
          <Header
            health={health}
            config={config}
            onRefreshConfig={loadMetadata}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />

          {/* Hero — shown on first load */}
          {showHero && activeTab === 'studio' && (
            <Hero onGetStarted={handleGetStarted} />
          )}

          {activeTab === 'studio' && (
            <div>
              <RecordingControl
                devices={devices}
                recordingStatus={recordingStatus}
                liveSegments={liveSegments}
                onStartRecording={handleStartRecording}
                onStopRecording={handleStopRecording}
              />

              <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '24px', minHeight: '480px' }}>
                <MeetingList
                  meetings={meetings}
                  selectedMeetingId={selectedMeetingId}
                  onSelectMeeting={(id) => {
                    setSelectedMeetingId(id);
                    setShowHero(false);
                  }}
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
                      borderRadius: 'var(--radius-lg)',
                      padding: '48px',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-muted)',
                      textAlign: 'center',
                    }}>
                      <div>
                        <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                          No Meeting Selected
                        </p>
                        <p style={{ fontSize: '0.85rem' }}>Select a past meeting from the list or start a new recording above.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'meetings' && (
            <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '24px', minHeight: '620px' }}>
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
                    borderRadius: 'var(--radius-lg)',
                    padding: '48px',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-muted)',
                    textAlign: 'center',
                  }}>
                    <p style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>Select a meeting from the archive list.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'actions' && (
            <ActionItemsHub meetings={meetings} />
          )}

          {activeTab === 'settings' && (
            <ProviderSettingsView config={config} onRefresh={loadMetadata} />
          )}
        </main>
      </div>
    </>
  );
}

export default App;
