import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginForm } from './components/LoginForm';
import { RegisterForm } from './components/RegisterForm';
import { MainPage } from './components/MainPage';
import PromptEditor from './components/PromptEditor';

type Page = 'main' | 'prompts';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [currentPage, setCurrentPage] = useState<Page>('main');

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        {isRegisterMode ? (
          <RegisterForm onSwitchToLogin={() => setIsRegisterMode(false)} />
        ) : (
          <LoginForm onSwitchToRegister={() => setIsRegisterMode(true)} />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <button
                onClick={() => setCurrentPage('main')}
                className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                  currentPage === 'main'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Создание карточек
              </button>
              <button
                onClick={() => setCurrentPage('prompts')}
                className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                  currentPage === 'prompts'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Редактирование промптов
              </button>
            </div>
            <div className="flex items-center">
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main>
        {currentPage === 'main' && <MainPage />}
        {currentPage === 'prompts' && <PromptEditor />}
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
