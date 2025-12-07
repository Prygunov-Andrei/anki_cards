import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Sparkles, Zap, Stars } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';

/**
 * Компактный селектор провайдера изображений для форм генерации
 * Можно выбрать "auto" (из профиля) или конкретный провайдер
 */

interface ImageProviderDropdownProps {
  value: 'auto' | 'openai' | 'gemini' | 'nano-banana';
  onChange: (provider: 'auto' | 'openai' | 'gemini' | 'nano-banana') => void;
  disabled?: boolean;
}

export const ImageProviderDropdown: React.FC<ImageProviderDropdownProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation();

  return (
    <div className="space-y-2">
      <label className="text-xs text-purple-700 dark:text-purple-300">
        {t.imageProviders.title}
      </label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="h-10 rounded-xl">
          <SelectValue placeholder={t.imageProviders.selectProvider} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="auto">
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">✨</span>
              <span>{t.imageProviders.auto}</span>
            </div>
          </SelectItem>
          <SelectItem value="openai">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#4FACFE]" />
              <span>{t.imageProviders.openai}</span>
            </div>
          </SelectItem>
          <SelectItem value="gemini">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-[#FF6B9D]" />
              <span>{t.imageProviders.gemini}</span>
            </div>
          </SelectItem>
          <SelectItem value="nano-banana">
            <div className="flex items-center gap-2">
              <Stars className="h-4 w-4 text-[#FFD93D]" />
              <span>{t.imageProviders.nanoBanana}</span>
            </div>
          </SelectItem>
        </SelectContent>
      </Select>
      {value === 'auto' && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t.imageProviders.autoHint}
        </p>
      )}
    </div>
  );
};