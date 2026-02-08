import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Wand2 } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';

interface ImageEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (mixin: string) => Promise<void>;
  word: string;
}

/**
 * Маленькое модальное окно для ввода миксина при редактировании изображения
 */
export const ImageEditModal: React.FC<ImageEditModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  word,
}) => {
  const t = useTranslation();
  const [mixin, setMixin] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!mixin.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(mixin.trim());
      setMixin('');
    } catch (error) {
      console.error('Error editing image:', error);
      // Ошибка обрабатывается в родительском компоненте через toast
    } finally {
      setIsSubmitting(false);
      onClose(); // Закрываем модальное окно после завершения операции (успешной или нет)
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isSubmitting && mixin.trim()) {
      handleSubmit();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-[350px] w-[90vw] sm:w-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Wand2 className="h-4 w-4 text-cyan-500" />
            {t.words.editImage}
          </DialogTitle>
        </DialogHeader>
        
        <div className="py-2">
          <p className="text-xs text-muted-foreground mb-2">
            {t.words.editImageHint}
          </p>
          <Input
            value={mixin}
            onChange={(e) => setMixin(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.words.editImagePlaceholder}
            disabled={isSubmitting}
            autoFocus
            maxLength={100}
          />
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={isSubmitting}
          >
            {t.common.cancel}
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || !mixin.trim()}
            className="bg-gradient-to-r from-cyan-500 to-pink-500 text-white"
          >
            {isSubmitting ? (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                {t.common.loading}
              </div>
            ) : (
              <>
                <Wand2 className="mr-1 h-3 w-3" />
                {t.words.editImageButton}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Default export для совместимости
export default ImageEditModal;