import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { translations, TranslationKeys, SupportedLocale } from '../locales';
import { useAuthContext } from './AuthContext';

interface LanguageContextType {
  locale: SupportedLocale;
  setLocale: (locale: SupportedLocale) => void;
  t: TranslationKeys;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const { user } = useAuthContext();
  const [locale, setLocaleState] = useState<SupportedLocale>('ru');

  // Синхронизируем язык интерфейса с родным языком пользователя
  useEffect(() => {
    if (user?.native_language) {
      const userLocale = user.native_language as SupportedLocale;
      if (translations[userLocale]) {
        setLocaleState(userLocale);
      }
    }
  }, [user?.native_language]);

  const setLocale = (newLocale: SupportedLocale) => {
    setLocaleState(newLocale);
  };

  const t = translations[locale] || translations.ru;

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

// Хук для удобного доступа только к переводам
export const useTranslation = () => {
  const { t } = useLanguage();
  return t;
};
