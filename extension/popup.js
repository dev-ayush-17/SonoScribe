// SonoScribe Extension — Popup Controller & Tab Audio Capture Engine

const BACKEND_URL = 'http://localhost:8000/api/v1';

let isRecording = false;
let mediaStream = null;
let audioContext = null;
let audioProcessor = null;
let recordedSamples = [];
let captureStartTime = 0;
let timerInterval = null;
let currentTabTitle = 'Google Meet / Tab Call';

const actionBtn = document.getElementById('actionBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const timerContainer = document.getElementById('timerContainer');
const timerText = document.getElementById('timerText');
const activeTabName = document.getElementById('activeTabName');
const messageBox = document.getElementById('messageBox');

function setStatus(state, label) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = label;
}

function showMessage(msg, isError = false) {
  messageBox.textContent = msg;
  messageBox.style.color = isError ? '#F87171' : '#34D399';
  messageBox.style.borderColor = isError ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)';
  messageBox.classList.remove('hidden');
}

function updateTimer() {
  const elapsedSeconds = Math.floor((Date.now() - captureStartTime) / 1000);
  const mins = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
  const secs = (elapsedSeconds % 60).toString().padStart(2, '0');
  timerText.textContent = `${mins}:${secs}`;
}

actionBtn.addEventListener('click', async () => {
  if (!isRecording) {
    await startTabCapture();
  } else {
    await stopTabCaptureAndTranscribe();
  }
});

async function startTabCapture() {
  setStatus('transcribing', 'Checking backend connection...');
  try {
    const healthRes = await fetch(`${BACKEND_URL}/health`);
    if (!healthRes.ok) throw new Error('Backend offline');
  } catch (err) {
    setStatus('idle', 'Backend Offline');
    showMessage('Please start the SonoScribe backend server at http://localhost:8000', true);
    return;
  }

  setStatus('transcribing', 'Requesting tab audio stream...');

  chrome.runtime.sendMessage({ type: 'GET_ACTIVE_TAB_STREAM_ID' }, async (response) => {
    if (!response || response.error) {
      setStatus('idle', 'Capture Failed');
      showMessage(response?.error || 'Failed to get tab stream', true);
      return;
    }

    currentTabTitle = response.tabTitle || 'Tab Session';
    activeTabName.textContent = `Target: ${currentTabTitle}`;

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          mandatory: {
            chromeMediaSource: 'tab',
            chromeMediaSourceId: response.streamId
          }
        },
        video: false
      });

      // ── CRITICAL: Reconnect captured stream to AudioContext destination so user STILL HEARS call ──
      audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = audioContext.createMediaStreamSource(mediaStream);
      source.connect(audioContext.destination); // Speaker passthrough!

      const bufferSize = 4096;
      audioProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      recordedSamples = [];

      audioProcessor.onaudioprocess = (e) => {
        if (!isRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        recordedSamples.push(new Float32Array(inputData));
      };

      source.connect(audioProcessor);
      audioProcessor.connect(audioContext.destination);

      isRecording = true;
      captureStartTime = Date.now();
      timerInterval = setInterval(updateTimer, 1000);

      setStatus('recording', 'Capturing Live Tab Audio...');
      actionBtn.textContent = 'Stop and Transcribe';
      actionBtn.classList.add('recording');
      timerContainer.classList.remove('hidden');
      messageBox.classList.add('hidden');

    } catch (err) {
      console.error('tabCapture error:', err);
      setStatus('idle', 'Error');
      showMessage(`Capture Error: ${err.message}`, true);
    }
  });
}

async function stopTabCaptureAndTranscribe() {
  isRecording = false;
  clearInterval(timerInterval);
  timerContainer.classList.add('hidden');

  setStatus('transcribing', 'Encoding & Transcribing...');
  actionBtn.disabled = true;

  if (audioProcessor) {
    audioProcessor.disconnect();
    audioProcessor = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
  if (audioContext) {
    await audioContext.close();
    audioContext = null;
  }

  let totalLength = 0;
  for (const chunk of recordedSamples) {
    totalLength += chunk.length;
  }
  const mergedSamples = new Float32Array(totalLength);
  let offset = 0;
  for (const chunk of recordedSamples) {
    mergedSamples.set(chunk, offset);
    offset += chunk.length;
  }

  if (mergedSamples.length === 0) {
    setStatus('idle', 'Empty Audio');
    showMessage('No audio collected during tab capture.', true);
    resetBtn();
    return;
  }

  const wavBlob = encodeWAV(mergedSamples, 16000);

  const formData = new FormData();
  formData.append('file', wavBlob, 'tab_capture.wav');
  formData.append('title', `Tab Capture — ${currentTabTitle}`);

  try {
    const response = await fetch(`${BACKEND_URL}/recording/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await response.json();
    setStatus('success', 'Transcribed & Saved!');
    showMessage(`Session "${data.title}" linked to dashboard!`);

  } catch (err) {
    console.error('Transcription upload error:', err);
    setStatus('idle', 'Upload Failed');
    showMessage(`Error: ${err.message}`, true);
  } finally {
    resetBtn();
  }
}

function resetBtn() {
  actionBtn.disabled = false;
  actionBtn.textContent = 'Start Capturing Tab';
  actionBtn.classList.remove('recording');
}

function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([buffer], { type: 'audio/wav' });
}
