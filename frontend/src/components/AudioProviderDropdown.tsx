import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Sparkles, Volume2 } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';

/**
 * Компактный селектор провайдера аудио для форм генерации
 * Можно выбрать "auto" (из профиля) или конкретный провайдер
 */

interface AudioProviderDropdownProps {
  value: 'auto' | 'openai' | 'gtts';
  onChange: (provider: 'auto' | 'openai' | 'gtts') => void;
  disabled?: boolean;
}

export const AudioProviderDropdown: React.FC<AudioProviderDropdownProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation();

  return (
    <div className="space-y-2">
      <label className="text-xs text-purple-700 dark:text-purple-300">
        {t.audioProviders.title}
      </label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="h-10 rounded-xl">
          <SelectValue placeholder={t.audioProviders.selectProvider} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="auto">
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">✨</span>
              <span>{t.audioProviders.auto}</span>
            </div>
          </SelectItem>
          <SelectItem value="openai">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#4FACFE]" />
              <span>{t.audioProviders.openai}</span>
            </div>
          </SelectItem>
          <SelectItem value="gtts">
            <div className="flex items-center gap-2">
              <Volume2 className="h-4 w-4 text-[#FFD93D]" />
              <span>{t.audioProviders.gtts}</span>
            </div>
          </SelectItem>
        </SelectContent>
      </Select>
      {value === 'auto' && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t.audioProviders.autoHint}
        </p>
      )}
    </div>
  );
};
