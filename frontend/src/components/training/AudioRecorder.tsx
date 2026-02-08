import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Send, X, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { useLanguage } from '../../contexts/LanguageContext';
import api from '../../services/api';
import { wordsService } from '../../services/words.service';

interface AudioRecorderProps {
  wordId: number;
  onRecorded: (audioUrl: string) => void;
  onClose: () => void;
}

/**
 * Компонент записи аудио с микрофона.
 * Использует MediaRecorder API.
 * После записи загружает файл на сервер и обновляет слово.
 */
export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  wordId,
  onRecorded,
  onClose,
}) => {
  const { t } = useLanguage();
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);

  const menu = t.trainingCard?.menu;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);

  const startRecording = async () => {
    setError(null);
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Choose best supported format
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Timer
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(menu?.microphoneError || 'Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
  };

  const handleUpload = async () => {
    if (!audioBlob) return;
    setIsUploading(true);
    setError(null);

    try {
      // Determine extension from MIME type
      const ext = audioBlob.type.includes('webm') ? '.webm' : audioBlob.type.includes('mp4') ? '.mp4' : '.webm';
      const fileName = `recording${ext}`;

      const formData = new FormData();
      formData.append('audio', audioBlob, fileName);

      const uploadRes = await api.post<{ audio_url: string; audio_id: string }>(
        '/api/media/upload-audio/',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      const uploadedUrl = uploadRes.data.audio_url;

      // Link audio to the word
      await wordsService.updateWord(wordId, { audio_file: uploadedUrl } as any);

      onRecorded(uploadedUrl);
      onClose();
    } catch {
      setError(menu?.uploadError || 'Failed to upload audio');
    } finally {
      setIsUploading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-card rounded-2xl shadow-xl p-6 w-80 max-w-[90vw] space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">
            {menu?.recordAudio || 'Record audio'}
          </h3>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Recording indicator */}
        <div className="flex flex-col items-center gap-3">
          {isRecording && (
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <span className="text-sm font-medium text-red-500">
                {menu?.recording || 'Recording...'} {formatTime(recordingTime)}
              </span>
            </div>
          )}

          {/* Playback preview */}
          {audioUrl && !isRecording && (
            <audio controls src={audioUrl} className="w-full" />
          )}

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        {/* Controls */}
        <div className="flex justify-center gap-3">
          {!isRecording && !audioBlob && (
            <Button onClick={startRecording} variant="default" className="gap-2">
              <Mic className="h-4 w-4" />
              {menu?.startRecording || 'Start'}
            </Button>
          )}

          {isRecording && (
            <Button onClick={stopRecording} variant="destructive" className="gap-2">
              <Square className="h-4 w-4" />
              {menu?.stopRecording || 'Stop'}
            </Button>
          )}

          {audioBlob && !isRecording && (
            <>
              <Button onClick={startRecording} variant="outline" className="gap-2">
                <Mic className="h-4 w-4" />
                {menu?.reRecord || 'Re-record'}
              </Button>
              <Button
                onClick={handleUpload}
                variant="default"
                className="gap-2"
                disabled={isUploading}
              >
                {isUploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                {menu?.send || 'Send'}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
