import React from 'react';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { AvatarUpload } from '../AvatarUpload';
import { getUserAvatarUrl } from '../../utils/url-helpers';
import { TranslationKeys } from '../../locales/ru';

interface ProfileBasicInfoProps {
  t: TranslationKeys;
  avatar: string | null | undefined;
  firstName: string;
  lastName: string;
  email: string;
  isLoading: boolean;
  onFieldChange: (field: string, value: string) => void;
  onAvatarChange: (file: File | null) => void;
  onAvatarRemove: () => void;
}

export const ProfileBasicInfo: React.FC<ProfileBasicInfoProps> = ({
  t,
  avatar,
  firstName,
  lastName,
  email,
  isLoading,
  onFieldChange,
  onAvatarChange,
  onAvatarRemove,
}) => {
  return (
    <>
      {/* Блок аватара */}
      <Card className="p-6">
        <h2 className="mb-6 text-xl text-gray-900 dark:text-gray-100">{t.profile.photoTitle}</h2>
        <AvatarUpload
          currentAvatar={getUserAvatarUrl(avatar)}
          onAvatarChange={onAvatarChange}
          onAvatarRemove={onAvatarRemove}
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
              value={firstName}
              onChange={(e) => onFieldChange('first_name', e.target.value)}
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
              value={lastName}
              onChange={(e) => onFieldChange('last_name', e.target.value)}
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
              value={email}
              onChange={(e) => onFieldChange('email', e.target.value)}
              className="h-12 rounded-xl"
              disabled={isLoading}
            />
          </div>
        </div>
      </Card>
    </>
  );
};
