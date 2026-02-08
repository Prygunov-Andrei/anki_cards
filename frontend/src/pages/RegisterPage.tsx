import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useState } from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import authService from '../services/authService';
import { showSuccess, showError } from '../utils/toast-helpers';
import { LanguageSelector } from '../components/LanguageSelector';

// Импортируем логотипы для светлой и темной темы
import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';

/**
 * Страница регистрации (всегда на английском языке)
 */
export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    nativeLanguage: 'en', // По умолчанию английский
    learningLanguage: 'de', // По умолчанию немецкий
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const { login } = useAuthContext();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Валидация формы
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Валидация username
    if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Only letters, numbers and underscore allowed';
    }

    // Валидация email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    // Валидация пароля
    if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    // Проверка совпадения паролей
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Валидация формы
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);

    try {
      const response = await authService.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        password_confirm: formData.confirmPassword,
        native_language: formData.nativeLanguage,
        learning_language: formData.learningLanguage,
        preferred_language: formData.nativeLanguage, // Для совместимости с бэкендом
      });
      login(response.token, response.user);
      showSuccess('Registration successful');
      navigate('/');
    } catch (error: unknown) {
      console.error('Register error:', error);
      
      // Обработка специфичных ошибок
      const errorMessage = error instanceof Error ? error.message : 'Registration error';
      if (errorMessage.includes('username')) {
        setErrors({ username: 'Username is already taken' });
        showError('Username is already taken');
      } else if (errorMessage.includes('email')) {
        setErrors({ email: 'Email is already in use' });
        showError('Email is already in use');
      } else {
        showError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Очистить ошибку для этого поля при изменении
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white dark:from-gray-950 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="w-20 h-20 mx-auto flex items-center justify-center">
              <img 
                src={isDark ? logoDark : logoLight} 
                alt="ANKI Generator Logo" 
                className="w-full h-full rounded-xl object-cover shadow-lg"
              />
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                placeholder="Choose a username"
                value={formData.username}
                onChange={(e) => handleChange('username', e.target.value)}
                className={`h-12 rounded-xl ${errors.username ? 'border-red-500' : ''}`}
                disabled={isLoading}
                required
                minLength={3}
              />
              {errors.username && (
                <p className="text-xs text-red-500">{errors.username}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className={`h-12 rounded-xl ${errors.email ? 'border-red-500' : ''}`}
                disabled={isLoading}
                required
              />
              {errors.email && (
                <p className="text-xs text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                placeholder="Create a password (min 6 characters)"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                className={`h-12 rounded-xl ${errors.password ? 'border-red-500' : ''}`}
                disabled={isLoading}
                required
                minLength={6}
              />
              {errors.password && (
                <p className="text-xs text-red-500">{errors.password}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                name="confirm-password"
                type="password"
                autoComplete="new-password"
                placeholder="Repeat password"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                className={`h-12 rounded-xl ${errors.confirmPassword ? 'border-red-500' : ''}`}
                disabled={isLoading}
                required
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-500">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Разделитель */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Language Settings
              </p>
              
              {/* Родной язык */}
              <div className="mb-4">
                <LanguageSelector
                  label="Native Language"
                  value={formData.nativeLanguage}
                  onChange={(value) => handleChange('nativeLanguage', value)}
                  placeholder="Select your native language"
                  disabled={isLoading}
                  type="native"
                />
              </div>

              {/* Изучаемый язык */}
              <LanguageSelector
                label="Learning Language"
                value={formData.learningLanguage}
                onChange={(value) => handleChange('learningLanguage', value)}
                excludeLanguages={[formData.nativeLanguage]} // Исключаем родной язык
                placeholder="Select language you want to learn"
                disabled={isLoading}
                type="learning"
              />
            </div>
            
            <Button 
              type="submit"
              className="w-full h-12 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl"
              disabled={isLoading}
            >
              {isLoading ? 'Creating account...' : 'Sign Up'}
            </Button>
          </form>

          <div className="text-center text-sm">
            <span className="text-gray-500 dark:text-gray-400">Already have an account? </span>
            <Link to="/login" className="text-purple-600 dark:text-purple-400">
              Log In
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}