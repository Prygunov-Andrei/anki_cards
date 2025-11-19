import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PromptEditor from '../PromptEditor';
import { apiService } from '../../services/api';

// Mock API service
jest.mock('../../services/api', () => ({
  apiService: {
    getUserPrompts: jest.fn(),
    getUserPrompt: jest.fn(),
    updateUserPrompt: jest.fn(),
    resetUserPrompt: jest.fn(),
  },
}));

const mockPrompts = [
  {
    id: 1,
    prompt_type: 'image',
    prompt_type_display: 'Генерация изображений',
    custom_prompt: 'Простое изображение слова {word}',
    is_custom: false,
    created_at: '2024-12-17T12:00:00Z',
    updated_at: '2024-12-17T12:00:00Z',
  },
  {
    id: 2,
    prompt_type: 'audio',
    prompt_type_display: 'Генерация аудио',
    custom_prompt: 'Произнеси слово {word}',
    is_custom: false,
    created_at: '2024-12-17T12:00:00Z',
    updated_at: '2024-12-17T12:00:00Z',
  },
];

describe('PromptEditor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiService.getUserPrompts as jest.Mock).mockResolvedValue(mockPrompts);
  });

  it('should render loading state initially', () => {
    render(<PromptEditor />);
    expect(screen.getByText('Загрузка промптов...')).toBeInTheDocument();
  });

  it('should load and display prompts', async () => {
    render(<PromptEditor />);
    
    await waitFor(() => {
      expect(apiService.getUserPrompts).toHaveBeenCalled();
    });

    expect(screen.getByText('Генерация изображений')).toBeInTheDocument();
    expect(screen.getByText('Генерация аудио')).toBeInTheDocument();
  });

  it('should expand prompt when clicked', async () => {
    render(<PromptEditor />);
    
    await waitFor(() => {
      expect(screen.getByText('Генерация изображений')).toBeInTheDocument();
    });

    const promptHeader = screen.getByText('Генерация изображений').closest('div');
    if (promptHeader) {
      fireEvent.click(promptHeader);
      
      await waitFor(() => {
        expect(screen.getByText('Промпт:')).toBeInTheDocument();
      });
    }
  });

  it('should save prompt when save button is clicked', async () => {
    (apiService.updateUserPrompt as jest.Mock).mockResolvedValue({
      ...mockPrompts[0],
      custom_prompt: 'Новый промпт',
      is_custom: true,
    });

    render(<PromptEditor />);
    
    await waitFor(() => {
      expect(screen.getByText('Генерация изображений')).toBeInTheDocument();
    });

    // Раскрываем промпт
    const promptHeader = screen.getByText('Генерация изображений').closest('div');
    if (promptHeader) {
      fireEvent.click(promptHeader);
      
      await waitFor(() => {
        const textarea = screen.getByPlaceholderText('Введите промпт...');
        expect(textarea).toBeInTheDocument();
        
        fireEvent.change(textarea, { target: { value: 'Новый промпт для {word}' } });
        
        const saveButton = screen.getByText('Сохранить');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(apiService.updateUserPrompt).toHaveBeenCalledWith(
          'image',
          { custom_prompt: 'Новый промпт для {word}' }
        );
      });
    }
  });

  it('should reset prompt when reset button is clicked', async () => {
    (apiService.resetUserPrompt as jest.Mock).mockResolvedValue({
      ...mockPrompts[0],
      is_custom: false,
    });

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    render(<PromptEditor />);
    
    await waitFor(() => {
      expect(screen.getByText('Генерация изображений')).toBeInTheDocument();
    });

    // Раскрываем промпт
    const promptHeader = screen.getByText('Генерация изображений').closest('div');
    if (promptHeader) {
      fireEvent.click(promptHeader);
      
      await waitFor(() => {
        const resetButton = screen.getByText('Сбросить до заводских');
        fireEvent.click(resetButton);
      });

      await waitFor(() => {
        expect(window.confirm).toHaveBeenCalled();
        expect(apiService.resetUserPrompt).toHaveBeenCalledWith('image');
      });
    }
  });

  it('should display error message on save failure', async () => {
    (apiService.updateUserPrompt as jest.Mock).mockRejectedValue({
      response: {
        data: { error: 'Ошибка валидации' },
      },
    });

    render(<PromptEditor />);
    
    await waitFor(() => {
      expect(screen.getByText('Генерация изображений')).toBeInTheDocument();
    });

    // Раскрываем промпт
    const promptHeader = screen.getByText('Генерация изображений').closest('div');
    if (promptHeader) {
      fireEvent.click(promptHeader);
      
      await waitFor(() => {
        const textarea = screen.getByPlaceholderText('Введите промпт...');
        fireEvent.change(textarea, { target: { value: 'Новый промпт' } });
        
        const saveButton = screen.getByText('Сохранить');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Ошибка валидации')).toBeInTheDocument();
      });
    }
  });
});

