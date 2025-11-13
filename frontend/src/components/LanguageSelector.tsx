import React, { useEffect } from 'react';
import { Language } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';

interface LanguageSelectorProps {
  value: Language;
  onChange: (language: Language) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ value, onChange }) => {
  const { user, updateUser } = useAuth();

  useEffect(() => {
    // Загружаем предпочитаемый язык из профиля при монтировании
    if (user?.preferred_language) {
      onChange(user.preferred_language);
    }
  }, [user, onChange]);

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLanguage = e.target.value as Language;
    onChange(newLanguage);

    // Сохраняем выбор в профиле пользователя
    if (user) {
      try {
        const updatedUser = await apiService.updateProfile({
          preferred_language: newLanguage,
        });
        updateUser(updatedUser);
      } catch (error) {
        console.error('Ошибка при обновлении профиля:', error);
      }
    }
  };

  return (
    <div>
      <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
        Язык
      </label>
      <select
        id="language"
        value={value}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="pt">Португальский</option>
        <option value="de">Немецкий</option>
      </select>
    </div>
  );
};

