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

// Импортируем логотипы для светлой и темной темы
import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';
import axios from 'axios';

/**
 * Страница входа (всегда на английском языке)
 */
export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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
    if (username.trim().length === 0) {
      newErrors.username = 'Please enter your username';
    }

    // Валидация пароля - при логине только проверяем, что не пустой
    if (password.length === 0) {
      newErrors.password = 'Please enter your password';
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

    console.log('[LoginPage] Attempting login with:', { username, password: '***' });

    try {
      console.log('[LoginPage] Calling authService.login...');
      const response = await authService.login({ username, password });
      console.log('[LoginPage] Login successful, response:', response);
      login(response.token, response.user);
      showSuccess(`Welcome back, ${response.user.username}!`);
      navigate('/');
    } catch (error: unknown) {
      console.error('[LoginPage] Login error:', error);
      if (axios.isAxiosError(error)) {
        console.error('[LoginPage] Error details:', {
          message: error.message,
          stack: error.stack,
          response: error.response
        });
      }
      
      // Обработка специфичных ошибок
      const errorMessage = error instanceof Error ? error.message : 'Login error';
      if (errorMessage.includes('Invalid credentials') || errorMessage.includes('401')) {
        setErrors({ password: 'Invalid credentials' });
        showError('Invalid credentials');
      } else if (errorMessage.includes('Network')) {
        showError('Could not connect to server');
      } else {
        showError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleUsernameChange = (value: string) => {
    setUsername(value);
    if (errors.username) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.username;
        return newErrors;
      });
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    if (errors.password) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.password;
        return newErrors;
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-950 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4">
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
                placeholder="Enter username"
                value={username}
                onChange={(e) => handleUsernameChange(e.target.value)}
                className={errors.username ? 'border-red-500' : ''}
                disabled={isLoading}
                required
              />
              {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                className={`h-12 rounded-xl ${errors.password ? 'border-red-500' : ''}`}
                disabled={isLoading}
                required
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
            </div>
            
            <Button 
              type="submit"
              className="w-full h-12 rounded-xl"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Log In'}
            </Button>
          </form>

          <div className="text-center text-sm">
            <span className="text-gray-500 dark:text-gray-400">Don't have an account? </span>
            <Link to="/register" className="text-blue-600 dark:text-blue-400">
              Sign Up
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}