import React from 'react';
import { Label } from '../ui/label';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface ProfilePromptSettingsProps {
  isOpen: boolean;
  onToggle: () => void;
  isLoading: boolean;
  hintPromptTemplate: string;
  sceneDescriptionPrompt: string;
  keywordExtractionPrompt: string;
  imagePromptTemplate: string;
  onFieldChange: (field: string, value: string) => void;
}

const promptFields = [
  {
    key: 'hint_prompt_template',
    label: 'Промпт подсказок',
    vars: '{word}, {translation}, {fragment_content}, {language_name}',
  },
  {
    key: 'scene_description_prompt',
    label: 'Промпт описания сцен',
    vars: '{fragment_content}',
  },
  {
    key: 'keyword_extraction_prompt',
    label: 'Промпт ключевых слов',
    vars: '{fragment_content}',
  },
  {
    key: 'image_prompt_template',
    label: 'Промпт изображений',
    vars: '{scene_description}',
  },
] as const;

export const ProfilePromptSettings: React.FC<ProfilePromptSettingsProps> = ({
  isOpen,
  onToggle,
  isLoading,
  hintPromptTemplate,
  sceneDescriptionPrompt,
  keywordExtractionPrompt,
  imagePromptTemplate,
  onFieldChange,
}) => {
  const values: Record<string, string> = {
    hint_prompt_template: hintPromptTemplate,
    scene_description_prompt: sceneDescriptionPrompt,
    keyword_extraction_prompt: keywordExtractionPrompt,
    image_prompt_template: imagePromptTemplate,
  };

  return (
    <div>
      <button
        type="button"
        className="flex w-full items-center gap-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300"
        onClick={onToggle}
      >
        {isOpen ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        Шаблоны промптов
        <span className="text-xs text-gray-400">(пустое = системный дефолт)</span>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-4">
          {promptFields.map(({ key, label, vars }) => (
            <div key={key} className="space-y-1">
              <Label className="text-sm">{label}</Label>
              <textarea
                value={values[key]}
                onChange={(e) => onFieldChange(key, e.target.value)}
                disabled={isLoading}
                rows={3}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm resize-y"
                placeholder="Пустое значение = системный дефолт"
              />
              <p className="text-xs text-gray-400">Переменные: {vars}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
