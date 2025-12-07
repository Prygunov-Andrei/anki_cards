import React from 'react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { Zap, Sparkles } from 'lucide-react';
import { GeminiModel, GeminiModelInfo } from '../types';
import { useTranslation } from '../contexts/LanguageContext';

interface GeminiModelSelectorProps {
  value: GeminiModel;
  onChange: (model: GeminiModel) => void;
  disabled?: boolean;
}

// Информация о моделях Gemini (только технические данные)
const GEMINI_MODELS_DATA: Array<{
  id: GeminiModel;
  cost: number;
  speed: string;
  icon: string;
}> = [
  {
    id: 'gemini-2.5-flash-image',
    cost: 0.5,
    speed: '~4.7 сек',
    icon: '⚡',
  },
  {
    id: 'nano-banana-pro-preview',
    cost: 1,
    speed: '~12.6 сек',
    icon: '🆕',
  },
];

/**
 * Компонент GeminiModelSelector - выбор модели Gemini для генерации изображений
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const GeminiModelSelector: React.FC<GeminiModelSelectorProps> = ({
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
      <Label className="text-sm font-medium">{t.media.geminiModel}</Label>
      
      <div className="grid gap-3">
        {GEMINI_MODELS_DATA.map((model) => {
          const isSelected = value === model.id;
          const Icon = model.id === 'gemini-2.5-flash-image' ? Zap : Sparkles;
          
          // Получаем переводы для конкретной модели
          const modelTranslations = model.id === 'gemini-2.5-flash-image'
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
                    ? 'border-2 border-cyan-500 bg-cyan-50 shadow-md' 
                    : 'border-2 border-transparent hover:border-gray-300 hover:shadow-sm'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  {/* Иконка модели */}
                  <div 
                    className={`
                      flex-shrink-0 rounded-full p-2.5 transition-colors
                      ${isSelected ? 'bg-cyan-500' : 'bg-gray-100'}
                    `}
                  >
                    <Icon 
                      className={`h-5 w-5 ${isSelected ? 'text-white' : 'text-gray-600'}`} 
                    />
                  </div>
                  
                  {/* Информация о модели */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <h4 className={`font-semibold ${isSelected ? 'text-cyan-900' : 'text-gray-900'}`}>
                        {modelTranslations.name}
                      </h4>
                      
                      {/* Стоимость */}
                      <div 
                        className={`
                          flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold
                          ${model.cost === 0.5 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                          }
                        `}
                      >
                        {getTokenLabel(model.cost)}
                      </div>
                    </div>
                    
                    {/* Описание */}
                    <p className="text-sm text-muted-foreground">
                      {modelTranslations.description}
                    </p>
                  </div>
                  
                  {/* Индикатор выбора */}
                  <div className="flex-shrink-0 flex items-center">
                    <div 
                      className={`
                        w-5 h-5 rounded-full border-2 transition-all
                        ${isSelected 
                          ? 'border-cyan-500 bg-cyan-500' 
                          : 'border-gray-300 bg-white'
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
      
      {/* Подсказка - можно добавить в переводы, но пока оставим как есть */}
      <p className="text-xs text-muted-foreground">
        💡 Gemini Flash дешевле и быстрее, Nano Banana Pro — новая модель с улучшенным качеством
      </p>
    </div>
  );
};

// Вспомогательная функция для получения стоимости модели
export const getGeminiModelCost = (model: GeminiModel): number => {
  const modelInfo = GEMINI_MODELS_DATA.find(m => m.id === model);
  return modelInfo?.cost || 1;
};

// Вспомогательная функция для получения информации о модели
export const getGeminiModelInfo = (model: GeminiModel): GeminiModelInfo | undefined => {
  const modelData = GEMINI_MODELS_DATA.find(m => m.id === model);
  if (!modelData) return undefined;
  
  // Здесь нужно будет получить переводы, но для совместимости с существующим API
  // возвращаем данные с русскими текстами как fallback
  return {
    id: modelData.id,
    name: modelData.id === 'gemini-2.5-flash-image' ? 'Gemini Flash' : 'Nano Banana Pro',
    description: modelData.id === 'gemini-2.5-flash-image' 
      ? 'Быстрая генерация ~4.7 сек' 
      : 'Новая модель, лучшее качество ~12.6 сек',
    cost: modelData.cost,
    speed: modelData.speed,
    icon: modelData.icon,
  };
};