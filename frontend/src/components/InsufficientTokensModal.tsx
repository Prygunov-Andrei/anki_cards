import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { AlertCircle, Coins, X } from 'lucide-react';
import { formatTokensWithText } from '../utils/token-formatting';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';

interface InsufficientTokensModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  requiredTokens: number;
}

/**
 * Компонент InsufficientTokensModal - модальное окно при недостаточном балансе токенов
 * Показывает информацию о текущем балансе и необходимости пополнения
 */
export const InsufficientTokensModal: React.FC<InsufficientTokensModalProps> = ({
  isOpen,
  onClose,
  currentBalance,
  requiredTokens,
}) => {
  const t = useTranslation();
  const { user } = useAuthContext();
  const [showContent, setShowContent] = useState(false);

  const sourceLang = user?.native_language || 'en';

  useEffect(() => {
    if (isOpen) {
      // Задержка для плавной анимации
      setTimeout(() => setShowContent(true), 100);
    } else {
      setShowContent(false);
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-red-100 to-orange-100 dark:from-red-950/30 dark:to-orange-950/30">
            <div
              className={`transition-all duration-500 ${
                showContent
                  ? 'scale-100 rotate-0 opacity-100'
                  : 'scale-0 -rotate-180 opacity-0'
              }`}
            >
              <AlertCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
            </div>
          </div>
          <DialogTitle className="text-center text-xl">
            {t.tokens.insufficientTokens}
          </DialogTitle>
          <DialogDescription className="text-center">
            {t.tokens.needMore}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Текущий баланс */}
          <div className="rounded-lg bg-gradient-to-br from-cyan-50 to-pink-50 p-4 dark:from-cyan-950/30 dark:to-pink-950/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Coins className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {t.tokens.yourBalance}:
                </span>
              </div>
              <span
                className={`text-lg font-semibold tabular-nums text-gray-900 dark:text-gray-100 transition-all duration-300 ${
                  showContent ? 'scale-100 opacity-100' : 'scale-80 opacity-0'
                }`}
              >
                {formatTokensWithText(currentBalance, t, sourceLang)}
              </span>
            </div>
          </div>

          {/* Необходимо токенов */}
          <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">
                {t.tokens.required}:
              </span>
              <span className="text-lg font-semibold tabular-nums text-gray-900 dark:text-gray-100">
                {formatTokensWithText(requiredTokens, t, sourceLang)}
              </span>
            </div>
          </div>

          {/* Информационное сообщение - пока оставим хардкод, т.к. это промо-текст */}
          <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950/30">
            <p className="text-sm text-blue-900 dark:text-blue-200">
              💡 <strong>Как получить токены:</strong>
              <br />
              • Регистрируйтесь и получите стартовый бонус
              <br />
              • Приглашайте друзей
              <br />
              • Участвуйте в акциях
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            onClick={onClose}
            className="w-full bg-gradient-to-r from-cyan-500 to-pink-500 text-white transition-all hover:from-cyan-600 hover:to-pink-600"
          >
            {t.common.close}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};