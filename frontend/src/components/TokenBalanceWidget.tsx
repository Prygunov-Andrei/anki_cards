import React, { useEffect, useState } from 'react';
import { Coins, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

interface TokenBalanceWidgetProps {
  balance: number;
  isLoading?: boolean;
  className?: string;
}

/**
 * Компонент TokenBalanceWidget - виджет отображения баланса токенов
 * Показывает текущий баланс с анимацией и предупреждением при низком балансе
 */
export const TokenBalanceWidget: React.FC<TokenBalanceWidgetProps> = ({
  balance,
  isLoading = false,
  className,
}) => {
  const [prevBalance, setPrevBalance] = useState(balance);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // Определяем состояние баланса (с проверкой на undefined)
  const isLowBalance = balance !== undefined && balance < 10 && balance > 0;
  const isZeroBalance = balance !== undefined && balance === 0;

  // Форматирование баланса с поддержкой дробных значений
  const formatBalance = (value: number | undefined): string => {
    // Если баланс не загружен, показываем 0
    if (value === undefined || value === null) {
      return '0';
    }
    // Если баланс целый, показываем без десятичных знаков
    if (value % 1 === 0) {
      return value.toLocaleString('ru-RU');
    }
    // Если дробный, показываем с одним десятичным знаком
    return value.toLocaleString('ru-RU', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
  };

  // Монтирование компонента
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Анимация при изменении баланса
  useEffect(() => {
    if (balance !== prevBalance && !isLoading) {
      setIsAnimating(true);
      const timer = setTimeout(() => {
        setIsAnimating(false);
        setPrevBalance(balance);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [balance, prevBalance, isLoading]);

  return (
    <div
      className={cn(
        'flex items-center space-x-2 rounded-full px-3 py-2 transition-all duration-200',
        isZeroBalance && 'bg-red-50 dark:bg-red-950/30',
        isLowBalance && !isZeroBalance && 'bg-yellow-50 dark:bg-yellow-950/30',
        !isLowBalance && !isZeroBalance && 'bg-gradient-to-r from-cyan-50 to-pink-50 dark:from-cyan-950/30 dark:to-pink-950/30',
        isMounted ? 'opacity-100 scale-100' : 'opacity-0 scale-90',
        className
      )}
    >
      {/* Иконка монеты с анимацией */}
      <div
        className="transition-transform duration-600"
        style={{
          transform: isAnimating ? 'rotate(360deg) scale(1.2)' : 'rotate(0deg) scale(1)',
          transition: isAnimating ? 'transform 0.6s ease-in-out' : 'transform 0.3s ease-in-out',
        }}
      >
        <Coins
          className={cn(
            'h-5 w-5 transition-colors',
            isZeroBalance && 'text-red-600 dark:text-red-400',
            isLowBalance && !isZeroBalance && 'text-yellow-600 dark:text-yellow-400',
            !isLowBalance && !isZeroBalance && 'text-cyan-500'
          )}
        />
      </div>

      {/* Баланс с анимацией */}
      <div className="flex items-center space-x-1">
        <span
          key={balance}
          className={cn(
            'text-sm font-semibold tabular-nums transition-all duration-300',
            isZeroBalance && 'text-red-600 dark:text-red-400',
            isLowBalance && !isZeroBalance && 'text-yellow-600 dark:text-yellow-400',
            !isLowBalance && !isZeroBalance && 'text-gray-900 dark:text-gray-100'
          )}
        >
          {isLoading ? '...' : formatBalance(balance)}
        </span>

        {/* Предупреждение при низком балансе */}
        {isLowBalance && !isLoading && (
          <div
            className="transition-all duration-300"
            style={{
              opacity: isMounted ? 1 : 0,
              transform: isMounted ? 'scale(1)' : 'scale(0)',
            }}
          >
            <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          </div>
        )}
      </div>
    </div>
  );
};