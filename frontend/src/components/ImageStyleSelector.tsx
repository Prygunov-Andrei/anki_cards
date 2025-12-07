import React from 'react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { Sparkles, Image, Palette } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';

export type ImageStyle = 'minimalistic' | 'balanced' | 'creative';

interface ImageStyleOption {
  value: ImageStyle;
  icon: React.ComponentType<{ className?: string }>;
  name: string;
  description: string;
  gradient: string;
}

interface ImageStyleSelectorProps {
  value: ImageStyle;
  onChange: (style: ImageStyle) => void;
  disabled?: boolean;
}

/**
 * Компонент ImageStyleSelector - выбор стиля генерируемых изображений
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const ImageStyleSelector: React.FC<ImageStyleSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation();

  /**
   * Варианты стилей изображений
   */
  const styles: Omit<ImageStyleOption, 'name' | 'description'>[] = [
    {
      value: 'minimalistic',
      icon: Image,
      gradient: 'from-gray-400 to-gray-600',
    },
    {
      value: 'balanced',
      icon: Palette,
      gradient: 'from-cyan-400 to-blue-500',
    },
    {
      value: 'creative',
      icon: Sparkles,
      gradient: 'from-pink-400 to-purple-500',
    },
  ];

  return (
    <div className="space-y-3">
      <Label>{t.imageStyles.title}</Label>
      
      <div className="grid gap-3 sm:grid-cols-3">
        {styles.map((style) => {
          const Icon = style.icon;
          const isSelected = value === style.value;

          return (
            <Card
              key={style.value}
              className={`
                relative cursor-pointer overflow-hidden p-4 transition-all duration-200
                ${isSelected
                  ? 'ring-2 ring-primary ring-offset-2 dark:ring-offset-gray-950'
                  : 'hover:shadow-md'
                }
                ${disabled ? 'cursor-not-allowed opacity-50' : ''}
              `}
              onClick={() => !disabled && onChange(style.value)}
            >
              {/* Выделение выбранного стиля */}
              {isSelected && (
                <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    strokeWidth="2"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}

              {/* Иконка с градиентом */}
              <div className="mb-3 flex justify-center">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${style.gradient}`}
                >
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>

              {/* Название */}
              <h3 className="mb-1 text-center font-medium text-gray-900 dark:text-gray-100">
                {t.imageStyles[style.value].name}
              </h3>

              {/* Описание */}
              <p className="text-center text-xs text-muted-foreground">
                {t.imageStyles[style.value].description}
              </p>
            </Card>
          );
        })}
      </div>
    </div>
  );
};