import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Language, WordMedia, ImageStyle } from '../types';
import { FileUpload } from './FileUpload';

interface MediaGeneratorProps {
  word: string;
  translation: string;
  language: Language;
  onMediaChange: (media: WordMedia) => void;
  imageStyle?: ImageStyle;
  initialMedia?: WordMedia;
}

export const MediaGenerator: React.FC<MediaGeneratorProps> = ({
  word,
  translation,
  language,
  onMediaChange,
  imageStyle = 'balanced',
  initialMedia,
}) => {
  console.log(`MediaGenerator [${word}]: компонент монтируется, initialMedia:`, initialMedia);
  console.log(`MediaGenerator [${word}]: onMediaChange тип:`, typeof onMediaChange);
  
  const [imageUrl, setImageUrl] = useState<string | undefined>(initialMedia?.imageUrl);
  const [audioUrl, setAudioUrl] = useState<string | undefined>(initialMedia?.audioUrl);
  const [imagePath, setImagePath] = useState<string | undefined>(initialMedia?.imagePath);
  const [audioPath, setAudioPath] = useState<string | undefined>(initialMedia?.audioPath);
  const [imageId, setImageId] = useState<string | undefined>(initialMedia?.imageId);
  const [audioId, setAudioId] = useState<string | undefined>(initialMedia?.audioId);

  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isUploadingAudio, setIsUploadingAudio] = useState(false);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');

  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [selectedAudioFile, setSelectedAudioFile] = useState<File | null>(null);

  const updateMedia = () => {
    const mediaData = {
      word,
      imageUrl,
      audioUrl,
      imageId,
      audioId,
      imagePath,
      audioPath,
    };
    console.log(`MediaGenerator [${word}]: updateMedia вызван с данными:`, mediaData);
    onMediaChange(mediaData);
  };

  // Инициализируем медиа при монтировании компонента только если есть initialMedia
  useEffect(() => {
    console.log(`MediaGenerator [${word}]: инициализация с initialMedia:`, initialMedia);
    // Вызываем onMediaChange только если есть initialMedia с данными
    if (initialMedia && (initialMedia.imagePath || initialMedia.audioPath)) {
      onMediaChange({
        word,
        imageUrl: initialMedia.imageUrl,
        audioUrl: initialMedia.audioUrl,
        imageId: initialMedia.imageId,
        audioId: initialMedia.audioId,
        imagePath: initialMedia.imagePath,
        audioPath: initialMedia.audioPath,
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleGenerateImage = async () => {
    console.log(`MediaGenerator [${word}]: handleGenerateImage вызван`);
    setIsGeneratingImage(true);
    setError('');
    try {
      const response = await apiService.generateImage(word, translation, language, imageStyle);
      console.log(`MediaGenerator [${word}]: ответ от API:`, response);
      if (response.dalle_prompt) {
        console.log(`MediaGenerator [${word}]: ========== ПРОМПТ ДЛЯ DALL-E ==========`);
        console.log(`MediaGenerator [${word}]:`, response.dalle_prompt);
        console.log(`MediaGenerator [${word}]: ======================================`);
      }
      if (response.image_url) {
        // Для медиафайлов используем базовый URL без /api/
        const baseUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace('/api', '');
        const fullUrl = response.image_url.startsWith('http')
          ? response.image_url
          : `${baseUrl}${response.image_url}`;
        setImageUrl(fullUrl);
        setImagePath(response.file_path);
        setImageId(response.image_id);
        setSelectedImageFile(null); // Очищаем выбранный файл
        setSuccessMessage('Изображение успешно сгенерировано!');
        setTimeout(() => setSuccessMessage(''), 3000);
        // Обновляем медиа с новыми значениями напрямую
        // Используем существующие значения из initialMedia, если текущие undefined
        const mediaData = {
          word,
          imageUrl: fullUrl,
          audioUrl: audioUrl || initialMedia?.audioUrl,
          imageId: response.image_id,
          audioId: audioId || initialMedia?.audioId,
          imagePath: response.file_path,
          audioPath: audioPath || initialMedia?.audioPath,
        };
        console.log(`MediaGenerator [${word}]: вызываю onMediaChange с данными:`, mediaData);
        onMediaChange(mediaData);
        console.log(`MediaGenerator [${word}]: onMediaChange вызван`);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error || err.message || 'Ошибка при генерации изображения'
      );
      setSuccessMessage('');
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const handleGenerateAudio = async () => {
    setIsGeneratingAudio(true);
    setError('');
    try {
      const response = await apiService.generateAudio(word, language);
      if (response.audio_url) {
        // Для медиафайлов используем базовый URL без /api/
        const baseUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace('/api', '');
        const fullUrl = response.audio_url.startsWith('http')
          ? response.audio_url
          : `${baseUrl}${response.audio_url}`;
        setAudioUrl(fullUrl);
        setAudioPath(response.file_path);
        setAudioId(response.audio_id);
        setSelectedAudioFile(null); // Очищаем выбранный файл
        setSuccessMessage('Аудио успешно сгенерировано!');
        setTimeout(() => setSuccessMessage(''), 3000);
        // Обновляем медиа с новыми значениями напрямую
        // Используем существующие значения из initialMedia, если текущие undefined
        onMediaChange({
          word,
          imageUrl: imageUrl || initialMedia?.imageUrl,
          audioUrl: fullUrl,
          imageId: imageId || initialMedia?.imageId,
          audioId: response.audio_id,
          imagePath: imagePath || initialMedia?.imagePath,
          audioPath: response.file_path,
        });
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error || err.message || 'Ошибка при генерации аудио'
      );
      setSuccessMessage('');
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  const handleUploadImage = async (file: File) => {
    setSelectedImageFile(file);
    setIsUploadingImage(true);
    setError('');
    try {
      const response = await apiService.uploadImage(file);
      if (response.image_url) {
        // Для медиафайлов используем базовый URL без /api/
        const baseUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace('/api', '');
        const fullUrl = response.image_url.startsWith('http')
          ? response.image_url
          : `${baseUrl}${response.image_url}`;
        setImageUrl(fullUrl);
        setImagePath(response.file_path);
        setImageId(response.image_id);
        setSuccessMessage('Изображение успешно загружено!');
        setTimeout(() => setSuccessMessage(''), 3000);
        // Обновляем медиа с новыми значениями напрямую
        // Используем существующие значения из initialMedia, если текущие undefined
        onMediaChange({
          word,
          imageUrl: fullUrl,
          audioUrl: audioUrl || initialMedia?.audioUrl,
          imageId: response.image_id,
          audioId: audioId || initialMedia?.audioId,
          imagePath: response.file_path,
          audioPath: audioPath || initialMedia?.audioPath,
        });
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error || err.message || 'Ошибка при загрузке изображения'
      );
      setSelectedImageFile(null);
      setSuccessMessage('');
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleUploadAudio = async (file: File) => {
    setSelectedAudioFile(file);
    setIsUploadingAudio(true);
    setError('');
    try {
      const response = await apiService.uploadAudio(file);
      if (response.audio_url) {
        // Для медиафайлов используем базовый URL без /api/
        const baseUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace('/api', '');
        const fullUrl = response.audio_url.startsWith('http')
          ? response.audio_url
          : `${baseUrl}${response.audio_url}`;
        setAudioUrl(fullUrl);
        setAudioPath(response.file_path);
        setAudioId(response.audio_id);
        setSuccessMessage('Аудио успешно загружено!');
        setTimeout(() => setSuccessMessage(''), 3000);
        // Обновляем медиа с новыми значениями напрямую
        // Используем существующие значения из initialMedia, если текущие undefined
        onMediaChange({
          word,
          imageUrl: imageUrl || initialMedia?.imageUrl,
          audioUrl: fullUrl,
          imageId: imageId || initialMedia?.imageId,
          audioId: response.audio_id,
          imagePath: imagePath || initialMedia?.imagePath,
          audioPath: response.file_path,
        });
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error || err.message || 'Ошибка при загрузке аудио'
      );
      setSelectedAudioFile(null);
      setSuccessMessage('');
    } finally {
      setIsUploadingAudio(false);
    }
  };

  const handleRemoveImage = () => {
    setImageUrl(undefined);
    setImagePath(undefined);
    setImageId(undefined);
    setSelectedImageFile(null);
    // Обновляем медиа с новыми значениями напрямую
    onMediaChange({
      word,
      imageUrl: undefined,
      audioUrl,
      imageId: undefined,
      audioId,
      imagePath: undefined,
      audioPath,
    });
  };

  const handleRemoveAudio = () => {
    setAudioUrl(undefined);
    setAudioPath(undefined);
    setAudioId(undefined);
    setSelectedAudioFile(null);
    // Обновляем медиа с новыми значениями напрямую
    onMediaChange({
      word,
      imageUrl,
      audioUrl: undefined,
      imageId,
      audioId: undefined,
      imagePath,
      audioPath: undefined,
    });
  };

  return (
    <div className="space-y-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{word}</h4>
        <span className="text-sm text-gray-500">{translation}</span>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-600">{successMessage}</p>
        </div>
      )}

      {/* Изображение */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleGenerateImage}
            disabled={isGeneratingImage || isUploadingImage}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            {isGeneratingImage ? 'Генерирую...' : 'Добавить картинку'}
          </button>
          {imageUrl && (
            <>
              <button
                type="button"
                onClick={handleGenerateImage}
                disabled={isGeneratingImage || isUploadingImage}
                className="px-3 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
              >
                Перегенерировать
              </button>
              <button
                type="button"
                onClick={handleRemoveImage}
                className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Удалить
              </button>
            </>
          )}
        </div>

        <FileUpload
          accept="image/jpeg,image/jpg,image/png"
          maxSize={10 * 1024 * 1024} // 10MB
          onFileSelect={handleUploadImage}
          onRemove={handleRemoveImage}
          currentFile={selectedImageFile}
          label="Или загрузить свой файл:"
          error={isUploadingImage ? 'Загружаю...' : undefined}
        />

        {imageUrl && (
          <div className="mt-2">
            <img
              src={imageUrl}
              alt={word}
              className="max-w-full h-auto max-h-32 rounded-md border border-gray-300"
            />
          </div>
        )}
      </div>

      {/* Аудио */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleGenerateAudio}
            disabled={isGeneratingAudio || isUploadingAudio}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            {isGeneratingAudio ? 'Генерирую...' : 'Добавить аудио'}
          </button>
          {audioUrl && (
            <>
              <button
                type="button"
                onClick={handleGenerateAudio}
                disabled={isGeneratingAudio || isUploadingAudio}
                className="px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
              >
                Перегенерировать
              </button>
              <button
                type="button"
                onClick={handleRemoveAudio}
                className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Удалить
              </button>
            </>
          )}
        </div>

        <FileUpload
          accept="audio/mpeg,audio/mp3"
          maxSize={5 * 1024 * 1024} // 5MB
          onFileSelect={handleUploadAudio}
          onRemove={handleRemoveAudio}
          currentFile={selectedAudioFile}
          label="Или загрузить свой файл:"
          error={isUploadingAudio ? 'Загружаю...' : undefined}
        />

        {audioUrl && (
          <div className="mt-2">
            <audio controls className="w-full max-w-md">
              <source src={audioUrl} type="audio/mpeg" />
              Ваш браузер не поддерживает аудио элемент.
            </audio>
          </div>
        )}
      </div>
    </div>
  );
};

