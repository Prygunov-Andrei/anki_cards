import api from './api';
import { TokenBalance, TokenTransaction } from '../types';

/**
 * Token Service - сервис для работы с токенами пользователя
 */
class TokenService {
  /**
   * Получить текущий баланс токенов
   * @returns Promise с балансом токенов
   */
  async getTokenBalance(): Promise<TokenBalance> {
    try {
      const response = await api.get<TokenBalance>('/api/tokens/balance/');
      return response.data;
    } catch (error) {
      console.error('Error fetching token balance:', error);
      throw error;
    }
  }

  /**
   * Получить историю транзакций токенов
   * @returns Promise с массивом транзакций
   */
  async getTokenTransactions(): Promise<TokenTransaction[]> {
    try {
      const response = await api.get<TokenTransaction[]>('/api/tokens/transactions/');
      return response.data;
    } catch (error) {
      console.error('Error fetching token transactions:', error);
      throw error;
    }
  }

  /**
   * Проверить достаточность баланса для операции
   * @param requiredAmount - необходимое количество токенов
   * @returns Promise<boolean> - true если баланс достаточен
   */
  async checkBalance(requiredAmount: number): Promise<boolean> {
    try {
      const { balance } = await this.getTokenBalance();
      return balance >= requiredAmount;
    } catch (error) {
      console.error('Error checking token balance:', error);
      return false;
    }
  }
}

export const tokenService = new TokenService();
