import React, { useState, useMemo, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useTokenContext } from '../contexts/TokenContext';
import { useTranslation } from '../contexts/LanguageContext';
import { getUserAvatarUrl } from '../utils/url-helpers';
import { Menu, X, User, LogOut, UserCircle, Plus, Layers, BookOpen, FolderTree, GraduationCap, Sun, Moon, Bell, TrendingDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from './ui/sheet';
import { VisuallyHidden } from './ui/visually-hidden';
import { TokenBalanceWidget } from './TokenBalanceWidget';

// Импортируем логотипы для светлой и темной темы
import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';

/**
 * Компонент Header - шапка приложения с навигацией
 */
export const Header: React.FC = () => {
  const { user, logout } = useAuthContext();
  const { theme, toggleTheme } = useTheme();
  const { balance, isLoading } = useTokenContext();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const t = useTranslation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { to: '/training', label: t.header.training, icon: GraduationCap },
    { to: '/words', label: t.header.words, icon: BookOpen },
    { to: '/categories', label: t.header.categories, icon: FolderTree },
    { to: '/decks', label: t.header.decks, icon: Layers },
    { to: '/forgetting-curve', label: t.header.forgettingCurve, icon: TrendingDown },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  // Инициалы пользователя для аватара
  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    return user?.username?.[0]?.toUpperCase() || 'U';
  };

  // Отображаемое имя пользователя
  const getDisplayName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    if (user?.first_name) {
      return user.first_name;
    }
    return user?.username || 'Пользователь';
  };

  // Мемоизируем URL аватара, чтобы избежать лишних вычислений
  const avatarUrl = useMemo(() => {
    return getUserAvatarUrl(user?.avatar) || undefined;
  }, [user?.avatar]);

  // Предзагрузка аватара для быстрого отображения
  useEffect(() => {
    if (avatarUrl) {
      const img = new Image();
      img.src = avatarUrl;
      // Принудительная загрузка в кэш браузера
      img.onload = () => {
        console.log('[Header] Avatar preloaded successfully:', avatarUrl);
      };
      img.onerror = () => {
        // Тихо игнорируем ошибку - fallback аватар все равно отобразится
        console.warn('[Header] Could not preload avatar (fallback will be used):', avatarUrl);
      };
    }
  }, [avatarUrl]);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200/50 bg-white/80 backdrop-blur-xl supports-[backdrop-filter]:bg-white/60 dark:border-gray-800/50 dark:bg-gray-950/80 dark:supports-[backdrop-filter]:bg-gray-950/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Логотип */}
          <Link to="/" className="flex items-center space-x-2 transition-opacity hover:opacity-80">
            <img
              src={theme === 'light' ? logoLight : logoDark}
              alt="ANKI Generator Logo"
              className="h-20 w-20 rounded-xl object-cover relative top-1 -left-1 md:top-0 md:left-0"
            />
            <span className="hidden text-xl font-semibold sm:inline-block dark:text-gray-100">
              ANKI Generator
            </span>
          </Link>

          {/* Desktop навигация */}
          <nav className="hidden items-center space-x-1 md:flex">
            {navLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center space-x-2 rounded-lg px-4 py-2 transition-all ${
                    isActive(link.to)
                      ? 'bg-blue-50 text-blue-600 shadow-sm dark:bg-blue-950/50 dark:text-blue-400'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Desktop профиль пользователя */}
          <div className="hidden items-center space-x-4 md:flex">
            {/* Переключатель темы */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-lg transition-all hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="Переключить тему"
            >
              {theme === 'light' ? (
                <Moon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              ) : (
                <Sun className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              )}
            </Button>

            {/* Виджет баланса токенов */}
            <TokenBalanceWidget balance={balance} isLoading={isLoading} />
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center space-x-2 rounded-full pr-4 transition-all hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={avatarUrl} />
                    <AvatarFallback className="bg-gradient-to-br from-cyan-400 to-pink-400 text-white">
                      {getUserInitials()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{getDisplayName()}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="font-medium">{user?.username}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/profile" className="flex cursor-pointer items-center">
                    <UserCircle className="mr-2 h-4 w-4" />
                    <span>{t.header.profile}</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/notifications" className="flex cursor-pointer items-center">
                    <Bell className="mr-2 h-4 w-4" />
                    <span>{t.header.notifications}</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="cursor-pointer text-red-600 focus:text-red-700"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>{t.header.logout}</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Mobile меню */}
          <div className="flex items-center space-x-4 md:hidden relative top-1">
            {/* Аватар (только для отображения) */}
            <div className="rounded-full">
              <Avatar className="h-11 w-11">
                <AvatarImage src={avatarUrl} />
                <AvatarFallback className="bg-gradient-to-br from-cyan-400 to-pink-400 text-white">
                  {getUserInitials()}
                </AvatarFallback>
              </Avatar>
            </div>

            {/* Mobile бургер-меню */}
            <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" className="p-2 h-auto w-auto hover:bg-transparent">
                  <Menu className="size-10" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <VisuallyHidden>
                  <SheetTitle>Меню навигации</SheetTitle>
                  <SheetDescription>
                    Навигация по приложению и настройки профиля
                  </SheetDescription>
                </VisuallyHidden>
                <div className="flex flex-col space-y-4 pt-8">
                  <div className="mb-4">
                    <div className="flex items-center space-x-3 rounded-lg bg-gradient-to-br from-cyan-50 to-pink-50 p-4 dark:from-cyan-950/30 dark:to-pink-950/30">
                      <Avatar className="h-16 w-16 ring-2 ring-white dark:ring-gray-800">
                        <AvatarImage src={avatarUrl} />
                        <AvatarFallback className="bg-gradient-to-br from-cyan-400 to-pink-400 text-white">
                          {getUserInitials()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex flex-col">
                        <span className="font-medium dark:text-gray-100">{getDisplayName()}</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</span>
                      </div>
                    </div>
                  </div>

                  {/* Баланс токенов в мобильном меню */}
                  <div className="flex justify-center">
                    <TokenBalanceWidget balance={balance} isLoading={isLoading} />
                  </div>

                  <nav className="flex flex-col space-y-2">
                    {navLinks.map((link) => {
                      const Icon = link.icon;
                      return (
                        <Link
                          key={link.to}
                          to={link.to}
                          onClick={() => setIsMobileMenuOpen(false)}
                          className={`flex items-center space-x-3 rounded-lg px-4 py-3 transition-all ${
                            isActive(link.to)
                              ? 'bg-blue-50 text-blue-600 shadow-sm dark:bg-blue-950/50 dark:text-blue-400'
                              : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'
                          }`}
                        >
                          <Icon className="h-5 w-5" />
                          <span>{link.label}</span>
                        </Link>
                      );
                    })}
                    
                    {/* Ссылка на Профиль */}
                    <Link
                      to="/profile"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`flex items-center space-x-3 rounded-lg px-4 py-3 transition-all ${
                        isActive('/profile')
                          ? 'bg-blue-50 text-blue-600 shadow-sm dark:bg-blue-950/50 dark:text-blue-400'
                          : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                    >
                      <UserCircle className="h-5 w-5" />
                      <span>{t.header.profile}</span>
                    </Link>
                    <Link
                      to="/notifications"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`flex items-center space-x-3 rounded-lg px-4 py-3 transition-all ${
                        isActive('/notifications')
                          ? 'bg-blue-50 text-blue-600 shadow-sm dark:bg-blue-950/50 dark:text-blue-400'
                          : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                    >
                      <Bell className="h-5 w-5" />
                      <span>{t.header.notifications}</span>
                    </Link>
                  </nav>

                  {/* Переключатель темы в мобильном меню */}
                  <Button
                    onClick={toggleTheme}
                    variant="outline"
                    className="w-full justify-start"
                  >
                    {theme === 'light' ? (
                      <>
                        <Moon className="mr-2 h-4 w-4" />
                        {t.header.dark}
                      </>
                    ) : (
                      <>
                        <Sun className="mr-2 h-4 w-4" />
                        {t.header.light}
                      </>
                    )}
                  </Button>

                  <div className="pt-4">
                    <Button
                      onClick={handleLogout}
                      variant="outline"
                      className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      {t.header.logout}
                    </Button>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
};