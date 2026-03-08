import React from 'react';
import { Card } from '../ui/card';
import { LanguageSelector } from '../LanguageSelector';
import { TranslationKeys } from '../../locales/ru';

interface ProfileLanguageSettingsProps {
  t: TranslationKeys;
  nativeLanguage: string;
  learningLanguage: string;
  isLoading: boolean;
  onFieldChange: (field: string, value: string) => void;
}

export const ProfileLanguageSettings: React.FC<ProfileLanguageSettingsProps> = ({
  t,
  nativeLanguage,
  learningLanguage,
  isLoading,
  onFieldChange,
}) => {
  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Родной язык */}
        <LanguageSelector
          label={t.profile.nativeLanguage}
          value={nativeLanguage}
          onChange={(value) => onFieldChange('native_language', value)}
          placeholder={t.profile.selectNativeLanguage}
          disabled={isLoading}
          type="native"
        />

        {/* Изучаемый язык */}
        <LanguageSelector
          label={t.profile.learningLanguage}
          value={learningLanguage}
          onChange={(value) => onFieldChange('learning_language', value)}
          excludeLanguages={[nativeLanguage]}
          placeholder={t.profile.selectLearningLanguage}
          disabled={isLoading}
          type="learning"
        />
      </div>
    </Card>
  );
};
