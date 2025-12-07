import React from 'react';
import { Card } from './ui/card';
import { Sparkles, Zap, Stars } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';

/**
 * Объединенный селектор моделей для генерации медиа
 * Выбор из трех моделей: DALL-E 3, Gemini Flash, Nano Banana Pro
 */

export type MediaModel = 'dalle3' | 'gemini-flash' | 'nano-banana';

interface MediaModelSelectorProps {
  value: MediaModel;
  onChange: (model: MediaModel) => void;
  disabled?: boolean;
}

interface ModelInfo {
  id: MediaModel;
  cost: number;
  icon: React.ComponentType<{ className?: string }>;
  gradient: string;
}

const MEDIA_MODELS: ModelInfo[] = [
  {
    id: 'dalle3',
    cost: 1,
    icon: Sparkles,
    gradient: 'from-[#4FACFE] to-[#00F2FE]', // Голубой
  },
  {
    id: 'gemini-flash',
    cost: 0.5,
    icon: Zap,
    gradient: 'from-[#FFD93D] to-[#FFA93D]', // Желтый
  },
  {
    id: 'nano-banana',
    cost: 1,
    icon: Stars,
    gradient: 'from-[#FF6B9D] to-[#FFC371]', // Розовый
  },
];

export const MediaModelSelector: React.FC<MediaModelSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation();

  // Функция для получения правильной формы слова "токен"
  const getTokenLabel = (cost: number): string => {
    if (cost === 1) {
      return `1 ${t.common.token}`;
    } else if (cost === 0.5) {
      return `0.5 ${t.common.tokens}`;
    }
    return `${cost} ${t.common.tokensMany}`;
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3">
        {MEDIA_MODELS.map((model) => {
          const isSelected = value === model.id;
          const Icon = model.icon;
          
          // Получаем переводы для конкретной модели
          const modelTranslations = model.id === 'dalle3' 
            ? t.mediaModels.dalle3
            : model.id === 'gemini-flash'
            ? t.mediaModels.geminiFlash
            : t.mediaModels.nanoBanana;
          
          return (
            <button
              key={model.id}
              type="button"
              onClick={() => !disabled && onChange(model.id)}
              disabled={disabled}
              className={`
                relative w-full text-left transition-all duration-200
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <Card
                className={`
                  p-4 transition-all duration-200
                  ${isSelected 
                    ? 'border-2 border-[#4FACFE] bg-gradient-to-br from-[#4FACFE]/5 to-transparent shadow-md' 
                    : 'border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  {/* Иконка модели */}
                  <div 
                    className={`
                      flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
                      bg-gradient-to-br ${model.gradient}
                    `}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  
                  {/* Информация о модели */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <h4 className={`font-semibold ${isSelected ? 'text-[#4FACFE]' : 'text-gray-900 dark:text-white'}`}>
                        {modelTranslations.name}
                      </h4>
                      
                      {/* Стоимость */}
                      <div 
                        className={`
                          flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold
                          ${model.cost === 0.5 
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                            : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                          }
                        `}
                      >
                        {getTokenLabel(model.cost)}
                      </div>
                    </div>
                    
                    {/* Описание */}
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {modelTranslations.description}
                    </p>
                  </div>
                  
                  {/* Индикатор выбора */}
                  <div className="flex-shrink-0 flex items-center">
                    <div 
                      className={`
                        w-5 h-5 rounded-full border-2 transition-all
                        ${isSelected 
                          ? 'border-[#4FACFE] bg-[#4FACFE]' 
                          : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
                        }
                      `}
                    >
                      {isSelected && (
                        <svg
                          className="w-full h-full text-white p-0.5"
                          fill="currentColor"
                          viewBox="0 0 12 12"
                        >
                          <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// Вспомогательные функции для конвертации между MediaModel и backend форматом

export const mediaModelToBackend = (model: MediaModel): {
  image_provider: 'openai' | 'gemini';
  gemini_model: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview';
} => {
  switch (model) {
    case 'dalle3':
      return {
        image_provider: 'openai',
        gemini_model: 'gemini-2.5-flash-image', // default, не используется
      };
    case 'gemini-flash':
      return {
        image_provider: 'gemini',
        gemini_model: 'gemini-2.5-flash-image',
      };
    case 'nano-banana':
      return {
        image_provider: 'gemini',
        gemini_model: 'nano-banana-pro-preview',
      };
  }
};

export const backendToMediaModel = (
  imageProvider: 'openai' | 'gemini',
  geminiModel: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
): MediaModel => {
  if (imageProvider === 'openai') {
    return 'dalle3';
  }
  
  if (geminiModel === 'gemini-2.5-flash-image') {
    return 'gemini-flash';
  }
  
  return 'nano-banana';
};

// Получить стоимость модели
export const getMediaModelCost = (model: MediaModel): number => {
  const modelInfo = MEDIA_MODELS.find(m => m.id === model);
  return modelInfo?.cost || 1;
};