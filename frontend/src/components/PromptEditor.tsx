import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { UserPrompt, PromptType } from '../types';

const PROMPT_TYPE_LABELS: Record<PromptType, string> = {
  image: 'Генерация изображений',
  audio: 'Генерация аудио',
  word_analysis: 'Анализ смешанных языков',
  translation: 'Перевод слов',
  deck_name: 'Генерация названия колоды',
  part_of_speech: 'Определение части речи',
  category: 'Определение категории',
};

const PLACEHOLDERS_INFO: Record<PromptType, string[]> = {
  image: ['{word}', '{translation}', '{native_language}', '{english_translation}'],
  audio: ['{word}', '{language}'],
  word_analysis: ['{learning_language}', '{native_language}'],
  translation: ['{learning_language}', '{native_language}'],
  deck_name: ['{learning_language}', '{native_language}'],
  part_of_speech: ['{word}', '{language}'],
  category: ['{word}', '{language}'],
};

const EXAMPLE_VALUES: Record<string, string> = {
  word: 'casa',
  translation: 'дом',
  language: 'pt',
  native_language: 'русском',
  learning_language: 'португальском',
  english_translation: 'house',
};

const PromptEditor: React.FC = () => {
  const [prompts, setPrompts] = useState<UserPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<Partial<Record<PromptType, boolean>>>({});
  const [errors, setErrors] = useState<Partial<Record<PromptType, string>>>({});
  const [selectedPromptType, setSelectedPromptType] = useState<PromptType | null>(null);
  const [editedPrompts, setEditedPrompts] = useState<Partial<Record<PromptType, string>>>({});

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const data = await apiService.getUserPrompts();
      setPrompts(data);
      
      // Инициализируем editedPrompts
      const initial: Record<PromptType, string> = {} as Record<PromptType, string>;
      data.forEach((prompt) => {
        initial[prompt.prompt_type] = prompt.custom_prompt;
      });
      setEditedPrompts(initial);
    } catch (error: any) {
      console.error('Ошибка при загрузке промптов:', error);
      setErrors({});
    } finally {
      setLoading(false);
    }
  };

  const handlePromptChange = (promptType: PromptType, value: string) => {
    setEditedPrompts((prev) => ({
      ...prev,
      [promptType]: value,
    }));
    // Очищаем ошибку при изменении
    if (errors[promptType]) {
      setErrors((prev) => ({
        ...prev,
        [promptType]: '',
      }));
    }
  };

  const handleSave = async (promptType: PromptType) => {
    try {
      setSaving((prev) => ({ ...prev, [promptType]: true }));
      setErrors((prev) => ({ ...prev, [promptType]: '' }));

      const promptText = editedPrompts[promptType] || '';
      const updatedPrompt = await apiService.updateUserPrompt(promptType, {
        custom_prompt: promptText,
      });

      // Обновляем промпт в списке
      setPrompts((prev) =>
        prev.map((p) => (p.prompt_type === promptType ? updatedPrompt : p))
      );

      // Показываем сообщение об успехе
      alert('Промпт успешно сохранен!');
    } catch (error: any) {
      console.error('Ошибка при сохранении промпта:', error);
      const errorMessage =
        error.response?.data?.error ||
        error.response?.data?.custom_prompt?.[0] ||
        'Ошибка при сохранении промпта';
      setErrors((prev) => ({
        ...prev,
        [promptType]: errorMessage,
      }));
    } finally {
      setSaving((prev) => ({ ...prev, [promptType]: false }));
    }
  };

  const handleReset = async (promptType: PromptType) => {
    if (!window.confirm('Вы уверены, что хотите сбросить промпт до заводских настроек?')) {
      return;
    }

    try {
      setSaving((prev) => ({ ...prev, [promptType]: true }));
      setErrors((prev) => ({ ...prev, [promptType]: '' }));

      const resetPrompt = await apiService.resetUserPrompt(promptType);

      // Обновляем промпт в списке и editedPrompts
      setPrompts((prev) =>
        prev.map((p) => (p.prompt_type === promptType ? resetPrompt : p))
      );
      setEditedPrompts((prev) => ({
        ...prev,
        [promptType]: resetPrompt.custom_prompt,
      }));

      alert('Промпт сброшен до заводских настроек!');
    } catch (error: any) {
      console.error('Ошибка при сбросе промпта:', error);
      const errorMessage =
        error.response?.data?.error || 'Ошибка при сбросе промпта';
      setErrors((prev) => ({
        ...prev,
        [promptType]: errorMessage,
      }));
    } finally {
      setSaving((prev) => ({ ...prev, [promptType]: false }));
    }
  };

  const getPreview = (promptType: PromptType, template: string): string => {
    const placeholders = PLACEHOLDERS_INFO[promptType];
    let preview = template;
    
    placeholders.forEach((placeholder) => {
      const key = placeholder.replace(/[{}]/g, '');
      const value = EXAMPLE_VALUES[key] || placeholder;
      preview = preview.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), value);
    });
    
    return preview;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">Загрузка промптов...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Редактирование промптов</h1>
      
      <div className="space-y-6">
        {prompts.map((prompt) => {
          const isExpanded = selectedPromptType === prompt.prompt_type;
          
          return (
            <div
              key={prompt.prompt_type}
              className="border border-gray-300 rounded-lg p-4 bg-white shadow-sm"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() =>
                  setSelectedPromptType(
                    isExpanded ? null : prompt.prompt_type
                  )
                }
              >
                <div className="flex items-center space-x-3">
                  <h2 className="text-xl font-semibold">
                    {PROMPT_TYPE_LABELS[prompt.prompt_type]}
                  </h2>
                  {prompt.is_custom && (
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      Пользовательский
                    </span>
                  )}
                </div>
                <button
                  className="text-gray-500 hover:text-gray-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedPromptType(
                      isExpanded ? null : prompt.prompt_type
                    );
                  }}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              </div>

              {isExpanded && (
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Промпт:
                    </label>
                    <textarea
                      value={editedPrompts[prompt.prompt_type] || ''}
                      onChange={(e) =>
                        handlePromptChange(prompt.prompt_type, e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={6}
                      placeholder="Введите промпт..."
                    />
                    {errors[prompt.prompt_type] && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors[prompt.prompt_type]}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Доступные плейсхолдеры:
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {PLACEHOLDERS_INFO[prompt.prompt_type].map((placeholder) => (
                        <span
                          key={placeholder}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm font-mono"
                        >
                          {placeholder}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Предпросмотр:
                    </label>
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-md text-sm text-gray-700">
                      {getPreview(
                        prompt.prompt_type,
                        editedPrompts[prompt.prompt_type] || ''
                      )}
                    </div>
                  </div>

                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleSave(prompt.prompt_type)}
                      disabled={saving[prompt.prompt_type]}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {saving[prompt.prompt_type] ? 'Сохранение...' : 'Сохранить'}
                    </button>
                    <button
                      onClick={() => handleReset(prompt.prompt_type)}
                      disabled={saving[prompt.prompt_type]}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Сбросить до заводских
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PromptEditor;

