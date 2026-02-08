import React from 'react';
import { Check } from 'lucide-react';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

export interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

/**
 * Все поддерживаемые языки (7 языков)
 */
export const ALL_LANGUAGES: Language[] = [
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
];

/**
 * Поддерживаемые языки для native_language (родной язык)
 * Все 8 языков полностью поддерживаются бэкендом
 */
export const NATIVE_LANGUAGES: Language[] = [
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
];

/**
 * Поддерживаемые языки для learning_language (изучаемый язык)
 * Все 8 языков полностью поддерживаются бэкендом
 */
export const LEARNING_LANGUAGES: Language[] = [
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
];

/**
 * Для обратной совместимости
 */
export const SUPPORTED_LANGUAGES = ALL_LANGUAGES;

/**
 * Получить язык по коду
 */
export const getLanguageByCode = (code: string): Language | undefined => {
  return ALL_LANGUAGES.find((lang) => lang.code === code);
};

/**
 * Валидация языкового кода для native_language
 */
export const isValidNativeLanguage = (code: string): boolean => {
  return NATIVE_LANGUAGES.some((lang) => lang.code === code);
};

/**
 * Валидация языкового кода для learning_language
 */
export const isValidLearningLanguage = (code: string): boolean => {
  return LEARNING_LANGUAGES.some((lang) => lang.code === code);
};

interface LanguageSelectorProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  excludeLanguages?: string[]; // Исключить определенные языки из списка
  placeholder?: string;
  disabled?: boolean;
  type?: 'native' | 'learning'; // Тип селектора: для родного или изучаемого языка
}

/**
 * Компонент селектора языка с флагами
 * iOS 25 стиль
 */
export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  label,
  value,
  onChange,
  excludeLanguages = [],
  placeholder = 'Выберите язык',
  disabled = false,
  type = 'native',
}) => {
  // Выбираем правильный список языков в зависимости от типа
  const baseLanguages = type === 'learning' ? LEARNING_LANGUAGES : NATIVE_LANGUAGES;
  
  // Фильтруем языки, если нужно исключить некоторые
  const availableLanguages = baseLanguages.filter(
    (lang) => !excludeLanguages.includes(lang.code)
  );

  // Получаем выбранный язык
  const selectedLanguage = getLanguageByCode(value);

  return (
    <div className="space-y-2">
      <Label htmlFor={`language-${label}`}>{label}</Label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          id={`language-${label}`}
          className="h-12 rounded-xl"
        >
          <SelectValue placeholder={placeholder}>
            {selectedLanguage && (
              <div className="flex items-center gap-3">
                <span className="text-2xl">{selectedLanguage.flag}</span>
                <span>{selectedLanguage.nativeName}</span>
              </div>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {availableLanguages.map((language) => (
            <SelectItem
              key={language.code}
              value={language.code}
              className="cursor-pointer py-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{language.flag}</span>
                <div className="flex flex-col">
                  <span className="font-medium">{language.nativeName}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {language.name}
                  </span>
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};