import React from 'react';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { ProfilePromptSettings } from './ProfilePromptSettings';

interface ProfileAISettingsProps {
  isOpen: boolean;
  onToggle: () => void;
  promptsOpen: boolean;
  onPromptsToggle: () => void;
  isLoading: boolean;
  hintGenerationModel: string;
  sceneDescriptionModel: string;
  matchingModel: string;
  keywordExtractionModel: string;
  hintTemperature: number;
  sceneDescriptionTemperature: number;
  matchingTemperature: number;
  keywordTemperature: number;
  elevenlabsVoiceId: string;
  hintPromptTemplate: string;
  sceneDescriptionPrompt: string;
  keywordExtractionPrompt: string;
  imagePromptTemplate: string;
  onFieldChange: (field: string, value: string | number) => void;
}

export const ProfileAISettings: React.FC<ProfileAISettingsProps> = ({
  isOpen,
  onToggle,
  promptsOpen,
  onPromptsToggle,
  isLoading,
  hintGenerationModel,
  sceneDescriptionModel,
  matchingModel,
  keywordExtractionModel,
  hintTemperature,
  sceneDescriptionTemperature,
  matchingTemperature,
  keywordTemperature,
  elevenlabsVoiceId,
  hintPromptTemplate,
  sceneDescriptionPrompt,
  keywordExtractionPrompt,
  imagePromptTemplate,
  onFieldChange,
}) => {
  const modelFields = [
    { key: 'hint_generation_model', label: 'Модель подсказок', value: hintGenerationModel },
    { key: 'scene_description_model', label: 'Модель описания сцен', value: sceneDescriptionModel },
    { key: 'matching_model', label: 'Модель матчинга', value: matchingModel },
    { key: 'keyword_extraction_model', label: 'Модель ключевых слов', value: keywordExtractionModel },
  ];

  const temperatureFields = [
    { key: 'hint_temperature', label: 'Подсказки', value: hintTemperature },
    { key: 'scene_description_temperature', label: 'Описание сцен', value: sceneDescriptionTemperature },
    { key: 'matching_temperature', label: 'Матчинг', value: matchingTemperature },
    { key: 'keyword_temperature', label: 'Ключевые слова', value: keywordTemperature },
  ];

  return (
    <Card className="p-6">
      <button
        type="button"
        className="flex w-full items-center justify-between text-left"
        onClick={onToggle}
      >
        <h2 className="text-xl text-gray-900 dark:text-gray-100">Настройки моделей ИИ</h2>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-500" />
        )}
      </button>

      {isOpen && (
        <div className="mt-6 space-y-6">
          {/* Модели LLM */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Модели LLM</h3>
            {modelFields.map(({ key, label, value }) => (
              <div key={key} className="flex items-center justify-between gap-4">
                <Label className="text-sm whitespace-nowrap">{label}</Label>
                <select
                  value={value}
                  onChange={(e) => onFieldChange(key, e.target.value)}
                  disabled={isLoading}
                  className="h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 text-sm"
                >
                  <option value="gpt-4o-mini">GPT-4o mini</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4.1-mini">GPT-4.1 mini</option>
                  <option value="gpt-4.1">GPT-4.1</option>
                </select>
              </div>
            ))}
          </div>

          {/* Температуры */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Температуры
              <span className="ml-2 text-xs text-gray-400">(0 = точный, 2 = креативный)</span>
            </h3>
            {temperatureFields.map(({ key, label, value }) => (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">{label}</Label>
                  <span className="text-xs text-gray-500 tabular-nums">{value.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={value}
                  onChange={(e) => onFieldChange(key, parseFloat(e.target.value))}
                  disabled={isLoading}
                  className="w-full accent-[#4FACFE]"
                />
              </div>
            ))}
          </div>

          {/* ElevenLabs Voice ID */}
          <div className="space-y-2">
            <Label className="text-sm">ElevenLabs Voice ID</Label>
            <Input
              type="text"
              placeholder="pNInz6obpgDQGcFmaJgB (по умолчанию)"
              value={elevenlabsVoiceId}
              onChange={(e) => onFieldChange('elevenlabs_voice_id', e.target.value)}
              disabled={isLoading}
              className="h-10 rounded-lg text-sm"
            />
            <p className="text-xs text-gray-400">Пустое значение = голос по умолчанию для языка</p>
          </div>

          {/* Prompt Templates */}
          <ProfilePromptSettings
            isOpen={promptsOpen}
            onToggle={onPromptsToggle}
            isLoading={isLoading}
            hintPromptTemplate={hintPromptTemplate}
            sceneDescriptionPrompt={sceneDescriptionPrompt}
            keywordExtractionPrompt={keywordExtractionPrompt}
            imagePromptTemplate={imagePromptTemplate}
            onFieldChange={onFieldChange}
          />
        </div>
      )}
    </Card>
  );
};
