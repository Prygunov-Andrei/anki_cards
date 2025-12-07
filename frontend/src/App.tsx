import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { TokenProvider } from './contexts/TokenContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Toaster } from './components/ui/sonner';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MainPage from './pages/MainPage';
import ProfilePage from './pages/ProfilePage';
import DecksPage from './pages/DecksPage';
import DeckEditorPage from './pages/DeckEditorPage';
import NotFoundPage from './pages/NotFoundPage';

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