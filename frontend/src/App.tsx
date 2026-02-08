import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MainPage from './pages/MainPage';
import ProfilePage from './pages/ProfilePage';
import DecksPage from './pages/DecksPage';
import DeckEditorPage from './pages/DeckEditorPage';
import WordDetailPage from './pages/WordDetailPage';
import WordsPage from './pages/WordsPage';
import CategoriesPage from './pages/CategoriesPage';
import TrainingDashboardPage from './pages/TrainingDashboardPage';
import TrainingStartPage from './pages/TrainingStartPage';
import TrainingSessionPage from './pages/TrainingSessionPage';
import NotificationSettingsPage from './pages/NotificationSettingsPage';
import ForgettingCurvePage from './pages/ForgettingCurvePage';
import NotFoundPage from './pages/NotFoundPage';

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { TokenProvider } from './contexts/TokenContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Toaster } from './components/ui/sonner';

/**
 * Главный компонент приложения ANKI Generator
 * iOS 25 стиль, оптимизирован для iPhone 17 Air
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemeProvider>
          <TokenProvider>
            <LanguageProvider>
              <Routes>
                {/* Публичные маршруты - доступны только неавторизованным */}
                <Route
                  path="/login"
                  element={
                    <PublicRoute>
                      <LoginPage />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/register"
                  element={
                    <PublicRoute>
                      <RegisterPage />
                    </PublicRoute>
                  }
                />

                {/* Защищённые маршруты - требуют авторизации */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <MainPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ProfilePage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/words"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <WordsPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/categories"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <CategoriesPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/decks"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DecksPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/decks/:id"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DeckEditorPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/training"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <TrainingDashboardPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/training/start"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <TrainingStartPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/training/session"
                  element={
                    <ProtectedRoute>
                      <TrainingSessionPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/forgetting-curve"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ForgettingCurvePage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <NotificationSettingsPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/words/:id"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <WordDetailPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                {/* 404 страница */}
                <Route path="/404" element={<NotFoundPage />} />
                <Route path="*" element={<Navigate to="/404" replace />} />
              </Routes>
              <Toaster position="top-center" richColors />
            </LanguageProvider>
          </TokenProvider>
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;