import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { tokenService } from '../services/token.service';
import { TokenBalance, TokenTransaction } from '../types';
import { useAuthContext } from './AuthContext';

interface TokenContextType {
  balance: number;
  isLoading: boolean;
  transactions: TokenTransaction[];
  fetchBalance: () => Promise<void>;
  fetchTransactions: () => Promise<void>;
  checkBalance: (requiredAmount: number) => Promise<boolean>;
  refreshBalance: () => Promise<void>;
}

const TokenContext = createContext<TokenContextType | undefined>(undefined);

/**
 * TokenProvider - провайдер контекста токенов
 * Управляет балансом токенов пользователя и историей транзакций
 */
export const TokenProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthContext();
  const [balance, setBalance] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [transactions, setTransactions] = useState<TokenTransaction[]>([]);

  /**
   * Получить баланс токенов
   */
  const fetchBalance = useCallback(async () => {
    if (!isAuthenticated) {
      setBalance(0);
      return;
    }

    try {
      setIsLoading(true);
      const data = await tokenService.getTokenBalance();
      setBalance(data.balance);
    } catch (error) {
      console.error('Failed to fetch token balance:', error);
      // В случае ошибки устанавливаем 0 (безопасное значение)
      setBalance(0);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  /**
   * Получить историю транзакций
   */
  const fetchTransactions = useCallback(async () => {
    if (!isAuthenticated) {
      setTransactions([]);
      return;
    }

    try {
      const data = await tokenService.getTokenTransactions();
      setTransactions(data);
    } catch (error) {
      console.error('Failed to fetch token transactions:', error);
      setTransactions([]);
    }
  }, [isAuthenticated]);

  /**
   * Проверить достаточность баланса
   */
  const checkBalance = useCallback(
    async (requiredAmount: number): Promise<boolean> => {
      // Сначала проверяем локальный баланс
      if (balance >= requiredAmount) {
        return true;
      }

      // Если локального баланса недостаточно, обновляем его с сервера
      await fetchBalance();
      return balance >= requiredAmount;
    },
    [balance, fetchBalance]
  );

  /**
   * Обновить баланс (принудительно)
   */
  const refreshBalance = useCallback(async () => {
    await fetchBalance();
  }, [fetchBalance]);

  // Загружаем баланс при монтировании компонента
  useEffect(() => {
    if (isAuthenticated) {
      fetchBalance();
    }
  }, [isAuthenticated, fetchBalance]);

  const value: TokenContextType = {
    balance,
    isLoading,
    transactions,
    fetchBalance,
    fetchTransactions,
    checkBalance,
    refreshBalance,
  };

  return <TokenContext.Provider value={value}>{children}</TokenContext.Provider>;
};

/**
 * Hook для использования контекста токенов
 */
export const useTokenContext = (): TokenContextType => {
  const context = useContext(TokenContext);
  if (!context) {
    throw new Error('useTokenContext must be used within a TokenProvider');
  }
  return context;
};
