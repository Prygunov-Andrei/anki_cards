import React from 'react';
import { PageHelpButton } from '../components/PageHelpButton';
import { Button } from '../components/ui/button';
import { useAuthContext } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/LanguageContext';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { languageBackendToCode } from '../utils/language-helpers';
import { useState, useEffect } from 'react';
import { MediaModel, mediaModelToBackend, backendToMediaModel } from '../components/MediaModelSelector';
import { ImageStyle } from '../components/ImageStyleSelector';
import { profileService } from '../services/profile.service';
import { logger } from '../utils/logger';
import { X } from 'lucide-react';
import { translations, SupportedLocale } from '../locales';
import axios from 'axios';

import { ProfileBasicInfo } from '../components/profile/ProfileBasicInfo';
import { ProfileLanguageSettings } from '../components/profile/ProfileLanguageSettings';
import { ProfileMediaSettings } from '../components/profile/ProfileMediaSettings';
import { ProfileAISettings } from '../components/profile/ProfileAISettings';

/**
 * Страница профиля пользователя
 * Полная форма редактирования с аватаром и языками
 */
export default function ProfilePage() {
  const { user, updateUser } = useAuthContext();
  const t = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [shouldRemoveAvatar, setShouldRemoveAvatar] = useState(false);

  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [promptsOpen, setPromptsOpen] = useState(false);

  const buildFormData = (u: NonNullable<typeof user>) => ({
    first_name: u.first_name || '',
    last_name: u.last_name || '',
    email: u.email || '',
    native_language: languageBackendToCode(u.native_language || 'ru'),
    learning_language: languageBackendToCode(u.learning_language || 'de'),
    media_model: backendToMediaModel(
      (u.image_provider || 'openai') as 'openai' | 'gemini',
      (u.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview'
    ),
    audio_provider: (u.audio_provider || 'openai') as 'openai' | 'gtts' | 'elevenlabs',
    image_style: (u.image_style || 'balanced') as ImageStyle,
    hint_generation_model: u.hint_generation_model || 'gpt-4o-mini',
    scene_description_model: u.scene_description_model || 'gpt-4o-mini',
    matching_model: u.matching_model || 'gpt-4o',
    keyword_extraction_model: u.keyword_extraction_model || 'gpt-4o-mini',
    hint_temperature: u.hint_temperature ?? 0.8,
    scene_description_temperature: u.scene_description_temperature ?? 0.5,
    matching_temperature: u.matching_temperature ?? 0.2,
    keyword_temperature: u.keyword_temperature ?? 0.3,
    elevenlabs_voice_id: u.elevenlabs_voice_id || '',
    hint_prompt_template: u.hint_prompt_template || '',
    scene_description_prompt: u.scene_description_prompt || '',
    keyword_extraction_prompt: u.keyword_extraction_prompt || '',
    image_prompt_template: u.image_prompt_template || '',
  });

  const [formData, setFormData] = useState(buildFormData(user || {} as NonNullable<typeof user>));

  useEffect(() => {
    if (user) setFormData(buildFormData(user));
  }, [user]);

  useEffect(() => {
    if (formData.learning_language === 'pt' && formData.audio_provider === 'openai') {
      setFormData((prev) => ({ ...prev, audio_provider: 'gtts' }));
    }
  }, [formData.learning_language]);

  const handleFieldChange = (field: string, value: string | number | MediaModel | ImageStyle) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAvatarChange = (file: File | null) => {
    setAvatarFile(file);
    setShouldRemoveAvatar(false);
  };

  const handleAvatarRemove = () => {
    setAvatarFile(null);
    setShouldRemoveAvatar(true);
  };

  const hasChanges = (): boolean => {
    if (!user) return false;
    const currentMediaModel = backendToMediaModel(
      (user.image_provider || 'openai') as 'openai' | 'gemini',
      (user.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview'
    );
    return (
      formData.first_name !== (user.first_name || '') ||
      formData.last_name !== (user.last_name || '') ||
      formData.email !== (user.email || '') ||
      formData.native_language !== languageBackendToCode(user.native_language || 'ru') ||
      formData.learning_language !== languageBackendToCode(user.learning_language || 'de') ||
      formData.media_model !== currentMediaModel ||
      formData.audio_provider !== (user.audio_provider || 'openai') ||
      formData.image_style !== (user.image_style || 'balanced') ||
      avatarFile !== null ||
      shouldRemoveAvatar
    );
  };

  const validateForm = (): boolean => {
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      showError(t.toast.invalidEmail, { description: t.toast.checkEmailFormat });
      return false;
    }
    if (formData.native_language === formData.learning_language) {
      showError(t.toast.languagesMismatch, { description: t.toast.languagesMustDiffer });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setIsLoading(true);

    try {
      const backendFormat = mediaModelToBackend(formData.media_model);
      const dataToSend = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        native_language: formData.native_language,
        learning_language: formData.learning_language,
        image_provider: backendFormat.image_provider,
        gemini_model: backendFormat.gemini_model,
        audio_provider: formData.audio_provider,
        image_style: formData.image_style,
        hint_generation_model: formData.hint_generation_model,
        scene_description_model: formData.scene_description_model,
        matching_model: formData.matching_model,
        keyword_extraction_model: formData.keyword_extraction_model,
        hint_temperature: formData.hint_temperature,
        scene_description_temperature: formData.scene_description_temperature,
        matching_temperature: formData.matching_temperature,
        keyword_temperature: formData.keyword_temperature,
        elevenlabs_voice_id: formData.elevenlabs_voice_id,
        hint_prompt_template: formData.hint_prompt_template,
        scene_description_prompt: formData.scene_description_prompt,
        keyword_extraction_prompt: formData.keyword_extraction_prompt,
        image_prompt_template: formData.image_prompt_template,
      };

      logger.log('Sending profile update:', dataToSend);
      let updatedUser;

      if (avatarFile || shouldRemoveAvatar) {
        if (shouldRemoveAvatar) {
          updatedUser = await profileService.removeAvatar();
          if (hasChanges()) {
            updatedUser = await profileService.updateProfile(dataToSend);
          }
        } else {
          updatedUser = await profileService.updateProfileWithAvatar(dataToSend, avatarFile);
        }
      } else {
        updatedUser = await profileService.updateProfile(dataToSend);
      }

      if (user) updateUser(updatedUser);
      setAvatarFile(null);
      setShouldRemoveAvatar(false);

      const newLocale = formData.native_language as SupportedLocale;
      const toastTranslations = translations[newLocale] || translations.ru;
      showSuccess(toastTranslations.toast.profileUpdated, {
        description: toastTranslations.toast.allChangesSaved,
      });
    } catch (error: unknown) {
      logger.error('Profile update error:', error);

      if (axios.isAxiosError(error)) {
        logger.error('Error response data:', error.response?.data);
        if (error.response?.status === 400) {
          const errorData = error.response.data;
          logger.error('Validation errors:', errorData);
          if (errorData.email) {
            showError(t.errors.invalidEmail, { description: errorData.email[0] || t.errors.invalidEmail });
          } else if (errorData.avatar) {
            showError(t.errors.unsupportedFormat, { description: errorData.avatar[0] || t.errors.useCorrectFormat });
          } else if (errorData.native_language) {
            logger.error('Native language error detail:', errorData.native_language);
            showError(t.errors.validation, { description: `Native language error: ${errorData.native_language[0] || 'Invalid'}` });
          } else if (errorData.learning_language) {
            logger.error('Learning language error detail:', errorData.learning_language);
            showError(t.errors.validation, { description: `Learning language error: ${errorData.learning_language[0] || 'Invalid'}` });
          } else if (errorData.image_provider) {
            showError(t.errors.validation, { description: errorData.image_provider[0] || 'Invalid image provider' });
          } else if (errorData.gemini_model) {
            showError(t.errors.validation, { description: errorData.gemini_model[0] || 'Invalid Gemini model' });
          } else if (errorData.audio_provider) {
            showError(t.errors.validation, { description: errorData.audio_provider[0] || 'Invalid audio provider' });
          } else {
            const errorMessage = JSON.stringify(errorData);
            showError(t.errors.validation, { description: errorMessage.length < 100 ? errorMessage : t.errors.validation });
          }
        } else if (error.response?.status === 401) {
          showError(t.errors.sessionExpired, { description: t.errors.pleaseLoginAgain });
        } else {
          showError(t.errors.generic, { description: t.errors.checkConnection });
        }
      } else {
        showError(t.errors.generic, { description: t.errors.checkConnection });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) setFormData(buildFormData(user));
    setAvatarFile(null);
    setShouldRemoveAvatar(false);
    showInfo(t.profile.changesCancelled);
  };

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-8 text-gray-900 dark:text-gray-100">{t.profile.title}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <ProfileBasicInfo
          t={t}
          avatar={user?.avatar}
          firstName={formData.first_name}
          lastName={formData.last_name}
          email={formData.email}
          isLoading={isLoading}
          onFieldChange={handleFieldChange}
          onAvatarChange={handleAvatarChange}
          onAvatarRemove={handleAvatarRemove}
        />

        <ProfileLanguageSettings
          t={t}
          nativeLanguage={formData.native_language}
          learningLanguage={formData.learning_language}
          isLoading={isLoading}
          onFieldChange={handleFieldChange}
        />

        <ProfileMediaSettings
          t={t}
          mediaModel={formData.media_model}
          imageStyle={formData.image_style}
          audioProvider={formData.audio_provider}
          learningLanguage={formData.learning_language}
          isLoading={isLoading}
          onFieldChange={handleFieldChange}
        />

        <ProfileAISettings
          isOpen={aiSettingsOpen}
          onToggle={() => setAiSettingsOpen(!aiSettingsOpen)}
          promptsOpen={promptsOpen}
          onPromptsToggle={() => setPromptsOpen(!promptsOpen)}
          isLoading={isLoading}
          hintGenerationModel={formData.hint_generation_model}
          sceneDescriptionModel={formData.scene_description_model}
          matchingModel={formData.matching_model}
          keywordExtractionModel={formData.keyword_extraction_model}
          hintTemperature={formData.hint_temperature}
          sceneDescriptionTemperature={formData.scene_description_temperature}
          matchingTemperature={formData.matching_temperature}
          keywordTemperature={formData.keyword_temperature}
          elevenlabsVoiceId={formData.elevenlabs_voice_id}
          hintPromptTemplate={formData.hint_prompt_template}
          sceneDescriptionPrompt={formData.scene_description_prompt}
          keywordExtractionPrompt={formData.keyword_extraction_prompt}
          imagePromptTemplate={formData.image_prompt_template}
          onFieldChange={handleFieldChange}
        />

        {/* Кнопки действий */}
        <div className="flex gap-3">
          <Button
            type="submit"
            className="h-12 flex-1 rounded-xl"
            disabled={isLoading || !hasChanges()}
          >
            {isLoading ? t.common.saving : t.common.save}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-12 flex-1 rounded-xl"
            onClick={handleCancel}
            disabled={isLoading || !hasChanges()}
          >
            <X className="mr-2 h-4 w-4" />
            {t.common.cancel}
          </Button>
        </div>

        {hasChanges() && (
          <p className="text-center text-sm text-orange-600 dark:text-orange-400">
            {t.profile.unsavedChanges}
          </p>
        )}
      </form>

      <PageHelpButton pageKey="profile" />
    </div>
  );
}
