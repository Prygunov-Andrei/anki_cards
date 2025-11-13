import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  AuthResponse,
  User,
  Word,
  CardGenerationRequest,
  CardGenerationResponse,
  ApiError,
  Language,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Добавляем токен к каждому запросу
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Token ${token}`;
      }
      return config;
    });

    // Обработка ошибок
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Токен истек или неверный
          localStorage.removeItem('token');
          // Не перенаправляем автоматически, пусть компоненты обрабатывают
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(
    username: string,
    email: string,
    password: string,
    preferred_language: Language
  ): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/auth/register/', {
      username,
      email,
      password,
      preferred_language,
    });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    return response.data;
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/auth/login/', {
      username,
      password,
    });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    return response.data;
  }

  logout(): void {
    localStorage.removeItem('token');
  }

  // User endpoints
  async getProfile(): Promise<User> {
    const response = await this.api.get<User>('/user/profile/');
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.api.patch<User>('/user/profile/', data);
    return response.data;
  }

  // Words endpoints
  async getWordsList(language?: Language, search?: string): Promise<Word[]> {
    const params: Record<string, string> = {};
    if (language) params.language = language;
    if (search) params.search = search;

    const response = await this.api.get<{ count: number; results: Word[] }>('/words/list/', {
      params,
    });
    return response.data.results;
  }

  // Cards endpoints
  async generateCards(
    data: CardGenerationRequest
  ): Promise<CardGenerationResponse> {
    const response = await this.api.post<CardGenerationResponse>(
      '/cards/generate/',
      data
    );
    return response.data;
  }

  async downloadCards(fileId: string): Promise<Blob> {
    const response = await this.api.get(`/cards/download/${fileId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const apiService = new ApiService();

