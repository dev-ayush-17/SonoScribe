export interface Meeting {
  id: string;
  title: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  status: 'recording' | 'completed' | 'failed';
  audio_device?: string;
  sample_rate: number;
  segment_count: number;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  id: string;
  meeting_id: string;
  segment_index: number;
  start_time: number;
  end_time: number;
  text: string;
  confidence?: number;
  provider: string;
  model?: string;
  status: string;
  language: string;
  created_at: string;
}

export interface ActionItem {
  task: string;
  owner: string;
  due_date: string;
}

export interface AiNote {
  id: string;
  meeting_id: string;
  provider: string;
  model?: string;
  summary?: string;
  decisions?: string[];
  action_items?: ActionItem[];
  open_questions?: string[];
  notable_timestamps?: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
}

export interface MeetingDetail extends Meeting {
  segments: TranscriptSegment[];
  ai_notes: AiNote[];
}

export interface RecordingStatus {
  is_recording: boolean;
  meeting_id?: string;
  status: 'idle' | 'recording' | 'transcribing' | 'paused' | 'error' | 'stopped';
  duration_seconds: number;
  segment_count: number;
  error?: string;
}

export interface AudioDevice {
  index: number;
  name: string;
  max_input_channels: number;
  max_output_channels: number;
  default_sample_rate: number;
  is_loopback: boolean;
  hostapi_name: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  platform: string;
  transcription_provider: string;
  transcription_available: boolean;
  ai_provider: string;
  ai_available: boolean;
  database: string;
}

export interface ProviderStatus {
  name: string;
  type: 'transcription' | 'ai';
  available: boolean;
  configured: boolean;
  error?: string;
}

export interface AppConfig {
  transcription: ProviderStatus;
  ai: ProviderStatus;
  audio_sample_rate: number;
  store_raw_audio: boolean;
}
