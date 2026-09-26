import type {
  AppConfig,
  AudioDevice,
  HealthStatus,
  Meeting,
  MeetingDetail,
  RecordingStatus,
  AiNote,
} from '../types';

const API_BASE = 'http://localhost:8000/api/v1';
const WS_BASE = 'ws://localhost:8000/ws/transcript';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch(`${API_BASE}/config`);
  if (!res.ok) throw new Error('Failed to fetch config');
  return res.json();
}

export async function fetchAudioDevices(): Promise<AudioDevice[]> {
  const res = await fetch(`${API_BASE}/recording/devices`);
  if (!res.ok) throw new Error('Failed to fetch audio devices');
  return res.json();
}

export async function fetchRecordingStatus(): Promise<RecordingStatus> {
  const res = await fetch(`${API_BASE}/recording/status`);
  if (!res.ok) throw new Error('Failed to fetch recording status');
  return res.json();
}

export async function startRecording(title: string, audioDevice?: string): Promise<{ meeting_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/recording/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, audio_device: audioDevice }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to start recording');
  }
  return res.json();
}

export async function stopRecording(): Promise<{ meeting_id: string; segment_count: number; duration_seconds: number }> {
  const res = await fetch(`${API_BASE}/recording/stop`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to stop recording');
  }
  return res.json();
}

export async function fetchMeetings(): Promise<Meeting[]> {
  const res = await fetch(`${API_BASE}/meetings`);
  if (!res.ok) throw new Error('Failed to fetch meetings');
  return res.json();
}

export async function fetchMeetingDetail(id: string): Promise<MeetingDetail> {
  const res = await fetch(`${API_BASE}/meetings/${id}`);
  if (!res.ok) throw new Error('Failed to fetch meeting detail');
  return res.json();
}

export async function deleteMeeting(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/meetings/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete meeting');
}

export async function generateAiNotes(meetingId: string, provider?: string): Promise<{ status: string; meeting_id: string; artifacts?: Record<string, string>; note?: AiNote }> {
  const res = await fetch(`${API_BASE}/meetings/${meetingId}/ai-notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to generate AI notes');
  }
  return res.json();
}

export async function exportTranscript(meetingId: string, format: 'markdown' | 'text' | 'json'): Promise<{ content: string; format: string }> {
  const res = await fetch(`${API_BASE}/meetings/${meetingId}/export?format=${format}`);
  if (!res.ok) throw new Error('Failed to export transcript');
  return res.json();
}

export function createTranscriptWebSocket(
  onSegment: (segment: any) => void,
  onStatus: (status: RecordingStatus) => void,
  onError?: (err: Event) => void
): WebSocket {
  const ws = new WebSocket(WS_BASE);

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'segment') {
        onSegment(msg.data);
      } else if (msg.type === 'status') {
        onStatus(msg.data);
      }
    } catch (e) {
      console.error('Failed to parse WS message:', e);
    }
  };

  if (onError) {
    ws.onerror = onError;
  }

  return ws;
}
