import React from 'react';
import { Check, Sparkles, Zap } from 'lucide-react';

/**
 * Селектор провайдера генерации изображений
 * iOS 25 дизайн с карточками провайдеров
 */

interface ImageProviderSelectorProps {
  value: 'openai' | 'gemini';
  onChange: (provider: 'openai' | 'gemini') => void;
  disabled?: boolean;
}

export const ImageProviderSelector: React.FC<ImageProviderSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const providers = [
    {
      id: 'openai' as const,
      name: 'OpenAI DALL-E 3',
      description: 'Высокое качество, детализированные изображения',
      icon: Sparkles,
      gradient: 'from-[#4FACFE] to-[#00F2FE]', // Голубой градиент
    },
    {
      id: 'gemini' as const,
      name: 'Google Gemini',
      description: 'Альтернативный провайдер, быстрая генерация',
      icon: Zap,
      gradient: 'from-[#FF6B9D] to-[#FFC371]', // Розово-желтый градиент
    },
  ];

  return (
    <div className="space-y-3">
      <label className="block">
        Провайдер генерации изображений
      </label>
      
      <div className="grid grid-cols-1 gap-3">
        {providers.map((provider) => {
          const isSelected = value === provider.id;
          const Icon = provider.icon;
          
          return (
            <button
              key={provider.id}
              type="button"
              onClick={() => !disabled && onChange(provider.id)}
              disabled={disabled}
              className={`
                relative overflow-hidden rounded-2xl p-4 text-left transition-all
                ${isSelected 
                  ? 'ring-2 ring-[#4FACFE] ring-offset-2 dark:ring-offset-gray-900' 
                  : 'ring-1 ring-gray-200 dark:ring-gray-700'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:ring-[#4FACFE]/50 cursor-pointer'}
                bg-white dark:bg-gray-800
              `}
            >
              {/* Градиентный фон для выбранной карточки */}
              {isSelected && (
                <div 
                  className={`absolute inset-0 bg-gradient-to-br ${provider.gradient} opacity-5`} 
                />
              )}
              
              <div className="relative flex items-start gap-3">
                {/* Иконка провайдера */}
                <div className={`
                  flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
                  bg-gradient-to-br ${provider.gradient}
                `}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                
                {/* Информация о провайдере */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-gray-900 dark:text-white">
                      {provider.name}
                    </h3>
                    {isSelected && (
                      <Check className="w-5 h-5 text-[#4FACFE] flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {provider.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      
      {/* Подсказка */}
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
        Провайдер по умолчанию будет использоваться для всех новых генераций. 
        Вы сможете изменить его при генерации отдельных изображений.
      </p>
    </div>
  );
};