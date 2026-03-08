import React from 'react';
import { Card } from '../ui/card';
import { Label } from '../ui/label';
import { MediaModelSelector, MediaModel } from '../MediaModelSelector';
import { ImageStyleSelector, ImageStyle } from '../ImageStyleSelector';
import { Volume2, Sparkles, Mic } from 'lucide-react';
import { TranslationKeys } from '../../locales/ru';

interface ProfileMediaSettingsProps {
  t: TranslationKeys;
  mediaModel: MediaModel;
  imageStyle: ImageStyle;
  audioProvider: 'openai' | 'gtts' | 'elevenlabs';
  learningLanguage: string;
  isLoading: boolean;
  onFieldChange: (field: string, value: string | MediaModel | ImageStyle) => void;
}

export const ProfileMediaSettings: React.FC<ProfileMediaSettingsProps> = ({
  t,
  mediaModel,
  imageStyle,
  audioProvider,
  learningLanguage,
  isLoading,
  onFieldChange,
}) => {
  return (
    <Card className="p-6">
      <h2 className="mb-6 text-xl text-gray-900 dark:text-gray-100">{t.profile.mediaGeneration}</h2>

      {/* Провайдер изображений */}
      <div className="mb-6">
        <Label className="mb-3 block text-sm text-gray-700 dark:text-gray-300">
          {t.profile.imageProvider}
        </Label>
        <MediaModelSelector
          value={mediaModel}
          onChange={(model) => onFieldChange('media_model', model)}
          disabled={isLoading}
        />
      </div>

      {/* Стиль изображений */}
      <div className="mb-6">
        <ImageStyleSelector
          value={imageStyle}
          onChange={(style) => onFieldChange('image_style', style)}
          disabled={isLoading}
        />
      </div>

      {/* Провайдер аудио */}
      <div>
        <Label className="mb-3 block text-sm text-gray-700 dark:text-gray-300">
          {t.profile.audioProvider}
        </Label>
        <div className="grid gap-3">
          {/* ElevenLabs */}
          <button
            type="button"
            onClick={() => !isLoading && onFieldChange('audio_provider', 'elevenlabs')}
            disabled={isLoading}
            className={`
              relative w-full text-left transition-all duration-200
              ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <Card
              className={`
                p-4 transition-all duration-200
                ${audioProvider === 'elevenlabs'
                  ? 'border-2 border-[#4FACFE] bg-gradient-to-br from-[#4FACFE]/5 to-transparent shadow-md'
                  : 'border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <div className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-lg
                  bg-gradient-to-br from-[#FF6B9D] to-[#FFC371]
                `}>
                  <Mic className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm text-gray-900 dark:text-gray-100">
                      ElevenLabs
                    </h3>
                    <span className="shrink-0 text-xs text-gray-600 dark:text-gray-400">
                      {t.profile.paid}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                    Высокое качество, естественный голос
                  </p>
                </div>
              </div>
            </Card>
          </button>

          {/* OpenAI TTS */}
          <button
            type="button"
            onClick={() => !isLoading && onFieldChange('audio_provider', 'openai')}
            disabled={isLoading}
            className={`
              relative w-full text-left transition-all duration-200
              ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <Card
              className={`
                p-4 transition-all duration-200
                ${audioProvider === 'openai'
                  ? 'border-2 border-[#4FACFE] bg-gradient-to-br from-[#4FACFE]/5 to-transparent shadow-md'
                  : 'border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <div className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-lg
                  bg-gradient-to-br from-[#4FACFE] to-[#00F2FE]
                `}>
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm text-gray-900 dark:text-gray-100">
                      {t.profile.openaiTTS}
                    </h3>
                    <span className="shrink-0 text-xs text-gray-600 dark:text-gray-400">
                      {t.profile.paid}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                    {t.profile.openaiTTSDescription}
                  </p>
                </div>
              </div>
            </Card>
          </button>

          {/* Google TTS (gTTS) */}
          <button
            type="button"
            onClick={() => !isLoading && onFieldChange('audio_provider', 'gtts')}
            disabled={isLoading}
            className={`
              relative w-full text-left transition-all duration-200
              ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <Card
              className={`
                p-4 transition-all duration-200
                ${audioProvider === 'gtts'
                  ? 'border-2 border-[#4FACFE] bg-gradient-to-br from-[#4FACFE]/5 to-transparent shadow-md'
                  : 'border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <div className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-lg
                  bg-gradient-to-br from-[#FFD93D] to-[#FFA93D]
                `}>
                  <Volume2 className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm text-gray-900 dark:text-gray-100">
                      {t.profile.googleTTS}
                    </h3>
                    <span className="shrink-0 text-xs text-gray-600 dark:text-gray-400">
                      {t.profile.free}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                    {t.profile.googleTTSDescription}
                  </p>
                </div>
              </div>
            </Card>
          </button>
        </div>

        {/* Подсказка для португальского */}
        {learningLanguage === 'pt' && audioProvider === 'openai' && (
          <div className="mt-3 rounded-lg bg-orange-50 dark:bg-orange-900/20 p-3 border border-orange-200 dark:border-orange-800">
            <p className="text-xs text-orange-800 dark:text-orange-200">
              {t.profile.portugueseWarning}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
