import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Loader2 } from 'lucide-react';
import { logger } from '../utils/logger';

interface CreateDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    name: string;
    target_lang: string;
    source_lang: string;
  }) => Promise<void>;
}

// Список поддерживаемых языков
const LANGUAGES = [
  { code: 'en', name: 'Английский', flag: '🇬🇧' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'es', name: 'Испанский', flag: '🇪🇸' },
  { code: 'fr', name: 'Французский', flag: '🇫🇷' },
  { code: 'de', name: 'Немецкий', flag: '🇩🇪' },
  { code: 'it', name: 'Итальянский', flag: '🇮🇹' },
  { code: 'pt', name: 'Португальский', flag: '🇵🇹' },
  { code: 'zh', name: 'Китайский', flag: '🇨🇳' },
  { code: 'ja', name: 'Японский', flag: '🇯🇵' },
  { code: 'ko', name: 'Корейский', flag: '🇰🇷' },
];

/**
 * Компонент CreateDeckModal - модальное окно создания колоды
 */
export const CreateDeckModal: React.FC<CreateDeckModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [targetLang, setTargetLang] = useState('en');
  const [sourceLang, setSourceLang] = useState('ru');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Валидация формы
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Введите название колоды';
    } else if (name.trim().length < 3) {
      newErrors.name = 'Название должно содержать минимум 3 символа';
    } else if (name.trim().length > 100) {
      newErrors.name = 'Название слишком длинное (макс. 100 символов)';
    }

    if (targetLang === sourceLang) {
      newErrors.languages = 'Язык изучения и язык перевода должны отличаться';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Обработчик отправки формы
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setIsLoading(true);
      await onSubmit({
        name: name.trim(),
        target_lang: targetLang,
        source_lang: sourceLang,
      });
      handleClose();
    } catch (error) {
      logger.error('Error creating deck:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Закрытие и сброс формы
  const handleClose = () => {
    setName('');
    setTargetLang('en');
    setSourceLang('ru');
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Создать новую колоду</DialogTitle>
          <DialogDescription>
            Введите название колоды и выберите языковую пару для изучения
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {/* Название колоды */}
            <div className="space-y-2">
              <Label htmlFor="deck-name">
                Название колоды <span className="text-red-500">*</span>
              </Label>
              <Input
                id="deck-name"
                placeholder="Например: Базовая лексика для путешествий"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (errors.name) {
                    setErrors({ ...errors, name: '' });
                  }
                }}
                className={errors.name ? 'border-red-500' : ''}
                disabled={isLoading}
                autoFocus
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name}</p>
              )}
            </div>

            {/* Язык изучения */}
            <div className="space-y-2">
              <Label htmlFor="target-lang">
                Язык изучения <span className="text-red-500">*</span>
              </Label>
              <Select
                value={targetLang}
                onValueChange={(value) => {
                  setTargetLang(value);
                  if (errors.languages) {
                    setErrors({ ...errors, languages: '' });
                  }
                }}
                disabled={isLoading}
              >
                <SelectTrigger id="target-lang">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center space-x-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Язык перевода */}
            <div className="space-y-2">
              <Label htmlFor="source-lang">
                Язык перевода <span className="text-red-500">*</span>
              </Label>
              <Select
                value={sourceLang}
                onValueChange={(value) => {
                  setSourceLang(value);
                  if (errors.languages) {
                    setErrors({ ...errors, languages: '' });
                  }
                }}
                disabled={isLoading}
              >
                <SelectTrigger id="source-lang">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center space-x-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.languages && (
                <p className="text-sm text-red-500">{errors.languages}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
            >
              Отмена
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Создать колоду
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
