/**
 * Сервис для работы с категориями (Этап 9).
 * API: /api/words/categories/
 */
import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import type {
  Category,
  CategoryTree,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  CategoryWordsResponse,
  WordCategoryRequest,
} from '../types';

class CategoriesService {
  /**
   * Получить дерево категорий (по умолчанию бэкенд возвращает дерево)
   */
  async getTree(): Promise<CategoryTree[]> {
    const response = await api.get<{ count: number; categories: CategoryTree[] }>(API_ENDPOINTS.CATEGORIES);
    return response.data.categories;
  }

  /**
   * Плоский список категорий
   */
  async getList(): Promise<Category[]> {
    const response = await api.get<{ count: number; categories: Category[] }>(API_ENDPOINTS.CATEGORIES, {
      params: { flat: 'true' },
    });
    return response.data.categories;
  }

  /**
   * Создать категорию
   */
  async create(data: CategoryCreateRequest): Promise<Category> {
    const response = await api.post<{ message: string; category: Category }>(API_ENDPOINTS.CATEGORIES, data);
    return response.data.category;
  }

  /**
   * Получить категорию по id
   */
  async getById(id: number): Promise<Category> {
    const response = await api.get<Category>(API_ENDPOINTS.CATEGORY_BY_ID(id));
    return response.data;
  }

  /**
   * Обновить категорию (PATCH)
   */
  async update(id: number, data: CategoryUpdateRequest): Promise<Category> {
    const response = await api.patch<{ message: string; category: Category }>(
      API_ENDPOINTS.CATEGORY_BY_ID(id),
      data
    );
    return response.data.category;
  }

  /**
   * Удалить категорию
   */
  async delete(id: number): Promise<void> {
    await api.delete(API_ENDPOINTS.CATEGORY_BY_ID(id));
  }

  /**
   * Получить слова в категории
   */
  async getWords(
    id: number,
    includeDescendants = true
  ): Promise<CategoryWordsResponse> {
    const response = await api.get<CategoryWordsResponse>(
      API_ENDPOINTS.CATEGORY_WORDS(id),
      { params: { include_descendants: includeDescendants } }
    );
    return response.data;
  }

  /**
   * Добавить слово в категорию
   */
  async addWordToCategory(
    wordId: number,
    categoryId: number
  ): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(
      API_ENDPOINTS.WORD_CATEGORIES(wordId),
      { category_id: categoryId } as WordCategoryRequest
    );
    return response.data;
  }

  /**
   * Удалить слово из категории
   */
  async removeWordFromCategory(
    wordId: number,
    categoryId: number
  ): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(
      API_ENDPOINTS.WORD_CATEGORIES(wordId),
      { data: { category_id: categoryId } as WordCategoryRequest }
    );
    return response.data;
  }
}

export const categoriesService = new CategoriesService();
