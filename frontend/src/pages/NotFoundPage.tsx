import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Home } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

/**
 * Страница 404 - не найдено
 */
export default function NotFoundPage() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-6">
      <div className="max-w-md text-center space-y-6">
        <div className="w-32 h-32 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full mx-auto flex items-center justify-center">
          <span className="text-6xl">🤔</span>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-4xl text-gray-900">404</h1>
          <h2 className="text-xl text-gray-700">{t.notFound.title}</h2>
          <p className="text-sm text-gray-500">
            {t.notFound.description}
          </p>
        </div>

        <Link to="/">
          <Button className="rounded-xl h-12 gap-2">
            <Home className="w-4 h-4" />
            {t.notFound.backToHome}
          </Button>
        </Link>

        <p className="text-xs text-gray-400 pt-4">
          {t.notFound.footer}
        </p>
      </div>
    </div>
  );
}
