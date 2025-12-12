import React from 'react';
import { Card } from './ui/card';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { ImageStyleSelector, ImageStyle } from './ImageStyleSelector';
import { ImageProviderDropdown } from './ImageProviderDropdown';
import { AudioProviderDropdown } from './AudioProviderDropdown';
import { Image, Volume2 } from 'lucide-react';

interface MediaSettingsProps {
  generateImages: boolean;
  generateAudio: boolean;
  imageStyle: ImageStyle;
  imageProvider?: 'auto' | 'openai' | 'gemini' | 'nano-banana'; // Опциональный провайдер
  audioProvider?: 'auto' | 'openai' | 'gtts'; // Опциональный провайдер аудио
  onGenerateImagesChange: (enabled: boolean) => void;
  onGenerateAudioChange: (enabled: boolean) => void;
  onImageStyleChange: (style: ImageStyle) => void;
  onImageProviderChange?: (provider: 'auto' | 'openai' | 'gemini' | 'nano-banana') => void; // Опциональный callback
  onAudioProviderChange?: (provider: 'auto' | 'openai' | 'gtts') => void; // Опциональный callback для аудио
  disabled?: boolean;
}

/**
 * Компонент MediaSettings - настройки генерации медиа-контента
 * Простой блок настроек для выбора типов медиа и стиля изображений
 * iOS 25 стиль
 */
export const MediaSettings: React.FC<MediaSettingsProps> = ({
  generateImages,
  generateAudio,
  imageStyle,
  imageProvider,
  audioProvider,
  onGenerateImagesChange,
  onGenerateAudioChange,
  onImageStyleChange,
  onImageProviderChange,
  onAudioProviderChange,
  disabled = false,
}) => {
  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 p-4 dark:border-purple-800 dark:from-purple-950/20 dark:to-pink-950/20">
      <div className="mb-4 flex items-center gap-2">
        <Image className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        <h3 className="font-semibold text-purple-900 dark:text-purple-100">
          Настройки медиа
        </h3>
      </div>

      <div className="space-y-4">
        {/* Генерация изображений */}
        <div className="flex items-center justify-between">
          <Label
            htmlFor="generate-images"
            className="cursor-pointer text-sm text-purple-900 dark:text-purple-100"
          >
            Генерировать изображения
          </Label>
          <Switch
            id="generate-images"
            checked={generateImages}
            onCheckedChange={onGenerateImagesChange}
            disabled={disabled}
          />
        </div>

        {/* Стиль изображений */}
        {generateImages && (
          <div className="ml-6 space-y-2">
            <Label className="text-xs text-purple-700 dark:text-purple-300">
              Стиль изображений
            </Label>
            <ImageStyleSelector
              value={imageStyle}
              onChange={onImageStyleChange}
              disabled={disabled}
            />
          </div>
        )}

        {/* Провайдер изображений (опционально) */}
        {generateImages && imageProvider !== undefined && onImageProviderChange && (
          <div className="ml-6 space-y-2">
            <ImageProviderDropdown
              value={imageProvider}
              onChange={onImageProviderChange}
              disabled={disabled}
            />
          </div>
        )}

        {/* Генерация аудио */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <Label
              htmlFor="generate-audio"
              className="cursor-pointer text-sm text-purple-900 dark:text-purple-100"
            >
              Генерировать аудио
            </Label>
          </div>
          <Switch
            id="generate-audio"
            checked={generateAudio}
            onCheckedChange={onGenerateAudioChange}
            disabled={disabled}
          />
        </div>

        {/* Провайдер аудио (опционально) */}
        {generateAudio && audioProvider !== undefined && onAudioProviderChange && (
          <div className="ml-6 space-y-2">
            <AudioProviderDropdown
              value={audioProvider}
              onChange={onAudioProviderChange}
              disabled={disabled}
            />
          </div>
        )}
      </div>
    </Card>
  );
};