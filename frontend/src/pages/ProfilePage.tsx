import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuthContext } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/LanguageContext';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { getUserAvatarUrl } from '../utils/url-helpers';
import { languageCodeToBackend, languageBackendToCode } from '../utils/language-helpers';
import { useState, useEffect } from 'react';
import { AvatarUpload } from '../components/AvatarUpload';
import { LanguageSelector, isValidNativeLanguage, isValidLearningLanguage } from '../components/LanguageSelector';
import { MediaModelSelector, MediaModel, mediaModelToBackend, backendToMediaModel } from '../components/MediaModelSelector';
import { profileService } from '../services/profile.service';
import { X } from 'lucide-react';
import { translations, SupportedLocale } from '../locales';

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
  
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    native_language: languageBackendToCode(user?.native_language || 'ru'),
    learning_language: languageBackendToCode(user?.learning_language || 'de'), // де по умолчанию, так как en не поддерживается для learning_language
    media_model: backendToMediaModel(
      (user?.image_provider || 'openai') as 'openai' | 'gemini',
      (user?.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
    ),
  });

  // Синхронизируем форму с данными пользователя
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        native_language: languageBackendToCode(user.native_language || 'ru'),
        learning_language: languageBackendToCode(user.learning_language || 'de'), // де по умолчанию, так как en не поддерживается для learning_language
        media_model: backendToMediaModel(
          (user.image_provider || 'openai') as 'openai' | 'gemini',
          (user.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
        ),
      });
    }
  }, [user]);

  /**
   * Обработка изменения аватара
   */
  const handleAvatarChange = (file: File | null) => {
    setAvatarFile(file);
    setShouldRemoveAvatar(false);
  };

  /**
   * Обработка удаления аватара
   */
  const handleAvatarRemove = () => {
    setAvatarFile(null);
    setShouldRemoveAvatar(true);
  };

  /**
   * Валидация формы
   */
  const validateForm = (): boolean => {
    // Email валидация
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      showError(t.toast.invalidEmail, {
        description: t.toast.checkEmailFormat,
      });
      return false;
    }

    // Языки не должны совпадать
    if (formData.native_language === formData.learning_language) {
      showError(t.toast.languagesMismatch, {
        description: t.toast.languagesMustDiffer,
      });
      return false;
    }

    return true;
  };

  /**
   * Отправка формы
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      let updatedUser;

      // Конвертируем media_model обратно в формат бэкенда
      const backendFormat = mediaModelToBackend(formData.media_model);
      const dataToSend = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        // ИСПРАВЛЕНО: Отправляем коды языков напрямую (ru, en, de и т.д.)
        // Бэкенд ожидает коды, а не полные названия!
        native_language: formData.native_language,
        learning_language: formData.learning_language,
        image_provider: backendFormat.image_provider,
        gemini_model: backendFormat.gemini_model,
      };

      // Логируем данные перед отправкой
      console.log('Sending profile update:', dataToSend);

      // Если есть файл аватара или нужно удалить аватар
      if (avatarFile || shouldRemoveAvatar) {
        if (shouldRemoveAvatar) {
          // Удаляем аватар
          updatedUser = await profileService.removeAvatar();
          // Затем обновляем остальные данные
          if (hasChanges()) {
            updatedUser = await profileService.updateProfile(dataToSend);
          }
        } else {
          // Загружаем с аватаром
          updatedUser = await profileService.updateProfileWithAvatar(
            dataToSend,
            avatarFile
          );
        }
      } else {
        // Обычное обновление без аватара
        updatedUser = await profileService.updateProfile(dataToSend);
      }

      // Обновляем пользователя в контексте
      if (user) {
        updateUser(updatedUser);
      }

      // Сбрасываем состояние аватара
      setAvatarFile(null);
      setShouldRemoveAvatar(false);

      // Используем переводы из нового языка для toast, если язык изменился
      // Это гарантирует, что toast всегда будет на правильном языке
      const newLocale = formData.native_language as SupportedLocale;
      const toastTranslations = translations[newLocale] || translations.ru;
      
      showSuccess(toastTranslations.toast.profileUpdated, {
        description: toastTranslations.toast.allChangesSaved,
      });
    } catch (error: any) {
      console.error('Profile update error:', error);
      console.error('Error response data:', error.response?.data);

      if (error.response?.status === 400) {
        const errorData = error.response.data;
        
        // Логируем все ошибки валидации
        console.error('Validation errors:', errorData);
        
        // Обрабатываем специфичные ошибки
        if (errorData.email) {
          showError(t.errors.invalidEmail, {
            description: errorData.email[0] || t.errors.invalidEmail,
          });
        } else if (errorData.avatar) {
          showError(t.errors.unsupportedFormat, {
            description: errorData.avatar[0] || t.errors.useCorrectFormat,
          });
        } else if (errorData.native_language) {
          console.error('Native language error detail:', errorData.native_language);
          showError(t.errors.validation, {
            description: `Native language error: ${errorData.native_language[0] || 'Invalid'}`,
          });
        } else if (errorData.learning_language) {
          console.error('Learning language error detail:', errorData.learning_language);
          showError(t.errors.validation, {
            description: `Learning language error: ${errorData.learning_language[0] || 'Invalid'}`,
          });
        } else if (errorData.image_provider) {
          showError(t.errors.validation, {
            description: errorData.image_provider[0] || 'Invalid image provider',
          });
        } else if (errorData.gemini_model) {
          showError(t.errors.validation, {
            description: errorData.gemini_model[0] || 'Invalid Gemini model',
          });
        } else {
          // Показываем общую ошибку с деталями
          const errorMessage = JSON.stringify(errorData);
          showError(t.errors.validation, {
            description: errorMessage.length < 100 ? errorMessage : t.errors.validation,
          });
        }
      } else if (error.response?.status === 401) {
        showError(t.errors.sessionExpired, {
          description: t.errors.pleaseLoginAgain,
        });
      } else {
        showError(t.errors.generic, {
          description: t.errors.checkConnection,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Отмена изменений
   */
  const handleCancel = () => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        native_language: languageBackendToCode(user.native_language || 'ru'),
        learning_language: languageBackendToCode(user.learning_language || 'de'), // де по умолчанию, так как en не поддерживается для learning_language
        media_model: backendToMediaModel(
          (user.image_provider || 'openai') as 'openai' | 'gemini',
          (user.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
        ),
      });
    }
    setAvatarFile(null);
    setShouldRemoveAvatar(false);
    showInfo(t.profile.changesCancelled);
  };

  /**
   * Проверка наличия изменений
   */
  const hasChanges = (): boolean => {
    if (!user) return false;
    
    const currentMediaModel = backendToMediaModel(
      (user.image_provider || 'openai') as 'openai' | 'gemini',
      (user.gemini_model || 'gemini-2.5-flash-image') as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
    );
    
    return (
      formData.first_name !== (user.first_name || '') ||
      formData.last_name !== (user.last_name || '') ||
      formData.email !== (user.email || '') ||
      formData.native_language !== languageBackendToCode(user.native_language || 'ru') ||
      formData.learning_language !== languageBackendToCode(user.learning_language || 'de') || // де по умолчанию, так как en не поддерживается для learning_language
      formData.media_model !== currentMediaModel ||
      avatarFile !== null ||
      shouldRemoveAvatar
    );
  };

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-8 text-gray-900 dark:text-gray-100">{t.profile.title}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Блок аватара */}
        <Card className="p-6">
          <h2 className="mb-6 text-xl text-gray-900 dark:text-gray-100">{t.profile.photoTitle}</h2>
          <AvatarUpload
            currentAvatar={getUserAvatarUrl(user?.avatar)}
            onAvatarChange={handleAvatarChange}
            onAvatarRemove={handleAvatarRemove}
          />
        </Card>

        {/* Блок личных данных */}
        <Card className="p-6">
          <div className="space-y-4">
            {/* Имя */}
            <div className="space-y-2">
              <Label htmlFor="first_name">{t.profile.firstName}</Label>
              <Input
                id="first_name"
                type="text"
                placeholder={t.profile.enterFirstName}
                value={formData.first_name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, first_name: e.target.value }))
                }
                className="h-12 rounded-xl"
                disabled={isLoading}
              />
            </div>

            {/* Фамилия */}
            <div className="space-y-2">
              <Label htmlFor="last_name">{t.profile.lastName}</Label>
              <Input
                id="last_name"
                type="text"
                placeholder={t.profile.enterLastName}
                value={formData.last_name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, last_name: e.target.value }))
                }
                className="h-12 rounded-xl"
                disabled={isLoading}
              />
            </div>

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">{t.profile.email}</Label>
              <Input
                id="email"
                type="email"
                placeholder={t.profile.enterEmail}
                value={formData.email}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, email: e.target.value }))
                }
                className="h-12 rounded-xl"
                disabled={isLoading}
              />
            </div>
          </div>
        </Card>

        {/* Блок языков */}
        <Card className="p-6">
          <div className="space-y-4">
            {/* Родной язык */}
            <LanguageSelector
              label={t.profile.nativeLanguage}
              value={formData.native_language}
              onChange={(value) =>
                setFormData((prev) => ({ ...prev, native_language: value }))
              }
              placeholder={t.profile.selectNativeLanguage}
              disabled={isLoading}
              type="native"
            />

            {/* Изучаемый язык */}
            <LanguageSelector
              label={t.profile.learningLanguage}
              value={formData.learning_language}
              onChange={(value) =>
                setFormData((prev) => ({ ...prev, learning_language: value }))
              }
              excludeLanguages={[formData.native_language]} // Исключаем родной язык
              placeholder={t.profile.selectLearningLanguage}
              disabled={isLoading}
              type="learning"
            />
          </div>
        </Card>

        {/* Блок генерации медиа */}
        <Card className="p-6">
          <h2 className="mb-6 text-xl text-gray-900 dark:text-gray-100">{t.profile.mediaGeneration}</h2>
          <MediaModelSelector
            value={formData.media_model}
            onChange={(model) =>
              setFormData((prev) => ({ ...prev, media_model: model }))
            }
            disabled={isLoading}
          />
        </Card>

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

        {/* Индикатор изменений */}
        {hasChanges() && (
          <p className="text-center text-sm text-orange-600 dark:text-orange-400">
            {t.profile.unsavedChanges}
          </p>
        )}
      </form>
    </div>
  );
}