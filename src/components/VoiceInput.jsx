import { useEffect, useRef, useState } from 'react';

const MODEL_ID = 'onnx-community/Voxtral-Mini-4B-Realtime-2602-ONNX';
const SAMPLE_RATE = 16000;
const MODEL_FILE_COUNT = 3;
const WORKLET_SOURCE = `
  class CaptureProcessor extends AudioWorkletProcessor {
    process(inputs) {
      const input = inputs[0];
      if (input.length && input[0].length) this.port.postMessage(input[0]);
      return true;
    }
  }
  registerProcessor('capture-processor', CaptureProcessor);
`;

let modelPromise;
let processorPromise;
let transformersPromise;
let BaseStreamer;

function waitUntil(condition) {
  return new Promise(resolve => {
    if (condition()) return resolve();
    const interval = setInterval(() => {
      if (condition()) {
        clearInterval(interval);
        resolve();
      }
    }, 50);
  });
}

export default function VoiceInput({ value, onChange, ...inputProps }) {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const audio = useRef(new Float32Array(0));
  const audioContext = useRef(null);
  const mediaStream = useRef(null);
  const worklet = useRef(null);
  const recording = useRef(false);
  const stopRequested = useRef(false);
  const originalValue = useRef('');
  const mounted = useRef(true);

  function cleanupAudio() {
    recording.current = false;
    worklet.current?.disconnect();
    worklet.current = null;
    mediaStream.current?.getTracks().forEach(track => track.stop());
    mediaStream.current = null;
    void audioContext.current?.close();
    audioContext.current = null;
  }

  useEffect(() => () => {
    mounted.current = false;
    stopRequested.current = true;
    cleanupAudio();
  }, []);

  async function loadModel() {
    if (!navigator.gpu) throw new Error('Voice input needs a browser with WebGPU support.');
    transformersPromise ||= import('@huggingface/transformers');
    const transformers = await transformersPromise;
    BaseStreamer = transformers.BaseStreamer;
    if (!modelPromise) {
      const files = new Map();
      modelPromise = transformers.VoxtralRealtimeForConditionalGeneration.from_pretrained(MODEL_ID, {
        dtype: { audio_encoder: 'q4f16', embed_tokens: 'q4f16', decoder_model_merged: 'q4f16' },
        device: 'webgpu',
        progress_callback: info => {
          if (info.status !== 'progress' || !info.file.endsWith('.onnx_data') || !info.total) return;
          files.set(info.file, info.loaded / info.total);
          const loaded = [...files.values()].reduce((sum, amount) => sum + amount, 0);
          if (mounted.current) setProgress(Math.min(Math.round(loaded / MODEL_FILE_COUNT * 100), 100));
        },
      }).catch(exception => {
        modelPromise = undefined;
        throw exception;
      });
    }
    if (!processorPromise) {
      processorPromise = transformers.VoxtralRealtimeProcessor.from_pretrained(MODEL_ID).catch(exception => {
        processorPromise = undefined;
        throw exception;
      });
    }
    return Promise.all([modelPromise, processorPromise]);
  }

  function appendAudio(samples) {
    const merged = new Float32Array(audio.current.length + samples.length);
    merged.set(audio.current);
    merged.set(samples, audio.current.length);
    audio.current = merged;
  }

  async function transcribe(model, processor) {
    const firstSampleCount = processor.num_samples_first_audio_chunk;
    await waitUntil(() => audio.current.length >= firstSampleCount || stopRequested.current);
    if (stopRequested.current) return;

    const firstInputs = await processor(audio.current.subarray(0, firstSampleCount), {
      is_streaming: true,
      is_first_audio_chunk: true,
    });
    const { hop_length: hopLength, n_fft: fftSize } = processor.feature_extractor.config;
    const halfWindow = Math.floor(fftSize / 2);
    const samplesPerToken = processor.audio_length_per_tok * hopLength;

    async function* features() {
      yield firstInputs.input_features;
      let melFrame = processor.num_mel_frames_first_audio_chunk;
      let start = melFrame * hopLength - halfWindow;
      while (!stopRequested.current) {
        const needed = start + processor.num_samples_per_audio_chunk;
        await waitUntil(() => audio.current.length >= needed || stopRequested.current);
        if (stopRequested.current) break;
        let end = needed;
        while (end + samplesPerToken <= audio.current.length) end += samplesPerToken;
        const chunk = await processor(audio.current.slice(start, end), {
          is_streaming: true,
          is_first_audio_chunk: false,
        });
        yield chunk.input_features;
        melFrame += chunk.input_features.dims[2];
        start = melFrame * hopLength - halfWindow;
      }
    }

    const specialIds = new Set(processor.tokenizer.all_special_ids.map(BigInt));
    let tokens = [];
    let isPrompt = true;
    const flush = () => {
      const text = processor.tokenizer.decode(tokens, { skip_special_tokens: true });
      const separator = originalValue.current && !originalValue.current.endsWith(' ') ? ' ' : '';
      onChange(`${originalValue.current}${separator}${text}`);
    };
    const streamer = new (class extends BaseStreamer {
      put(value) {
        if (stopRequested.current) return;
        if (isPrompt) { isPrompt = false; return; }
        if (value[0].length === 1 && specialIds.has(value[0][0])) return;
        tokens = tokens.concat(value[0]);
        flush();
      }
      end() { if (!stopRequested.current) flush(); }
    })();

    await model.generate({
      input_ids: firstInputs.input_ids,
      input_features: features(),
      max_new_tokens: 4096,
      streamer,
    });
  }

  async function start() {
    setError('');
    setProgress(0);
    setStatus('loading');
    try {
      const [model, processor] = await loadModel();
      if (!mounted.current) return;
      setProgress(100);
      originalValue.current = value;
      audio.current = new Float32Array(0);
      stopRequested.current = false;
      recording.current = true;
      setStatus('recording');

      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: SAMPLE_RATE } });
      mediaStream.current = stream;
      const context = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioContext.current = context;
      await context.resume();
      const source = context.createMediaStreamSource(stream);
      const silent = context.createGain();
      silent.gain.value = 0;
      const url = URL.createObjectURL(new Blob([WORKLET_SOURCE], { type: 'application/javascript' }));
      await context.audioWorklet.addModule(url);
      URL.revokeObjectURL(url);
      const node = new AudioWorkletNode(context, 'capture-processor');
      node.port.onmessage = event => recording.current && appendAudio(new Float32Array(event.data));
      source.connect(node);
      node.connect(silent);
      silent.connect(context.destination);
      worklet.current = node;
      await transcribe(model, processor);
    } catch (exception) {
      if (!stopRequested.current && mounted.current) setError(exception.message || 'Voice input failed.');
    } finally {
      cleanupAudio();
      if (mounted.current) setStatus('idle');
    }
  }

  function stop() {
    stopRequested.current = true;
    cleanupAudio();
    setStatus('idle');
  }

  const loading = status === 'loading';
  const listening = status === 'recording';
  const label = loading ? `Loading Voxtral${progress ? ` ${progress}%` : '…'}` : listening ? 'Stop listening' : 'Talk instead';

  return <>
    <div className="voice-input">
      <input value={value} onChange={onChange} {...inputProps} />
      <button
        className={`voice-button ${listening ? 'listening' : ''}`}
        type="button"
        onClick={listening ? stop : start}
        disabled={loading}
        aria-label={label}
        title={label}
      >{listening ? '■' : '●'}</button>
    </div>
    {(loading || listening) && <p className="voice-status" role="status">{loading ? `${label} · one-time ~2.8 GB download` : 'Listening locally… click stop when you’re done.'}</p>}
    {error && <p className="voice-error" role="alert">{error} You can keep typing.</p>}
  </>;
}
