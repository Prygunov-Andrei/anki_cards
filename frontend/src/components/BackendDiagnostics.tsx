import { useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import apiClient from '../services/api';
import { API_ENDPOINTS, API_BASE_URL } from '../lib/config';

interface DiagnosticResult {
  test: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  details?: any;
}

export function BackendDiagnostics() {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runDiagnostics = async () => {
    setIsRunning(true);
    const diagnostics: DiagnosticResult[] = [];

    // Тест 1: Проверка /health
    console.log('🧪 Test 1: Checking health endpoint');
    try {
      const response = await apiClient.get(API_ENDPOINTS.HEALTH);
      diagnostics.push({
        test: `GET ${API_ENDPOINTS.HEALTH}`,
        status: 'success',
        message: `✅ Успешно! Статус: ${response.status}`,
        details: response.data,
      });
    } catch (error: any) {
      diagnostics.push({
        test: `GET ${API_ENDPOINTS.HEALTH}`,
        status: 'error',
        message: `❌ Ошибка: ${error.code || error.message}`,
        details: {
          code: error.code,
          message: error.message,
          responseStatus: error.response?.status,
          responseData: error.response?.data,
        },
      });
    }

    // Тест 2: Проверка login endpoint (с тестовыми данными)
    console.log('🧪 Test 2: Checking login endpoint structure');
    try {
      const response = await apiClient.post(API_ENDPOINTS.LOGIN, {
        username: 'test_connection',
        password: 'test_connection',
      });
      diagnostics.push({
        test: `POST ${API_ENDPOINTS.LOGIN}`,
        status: 'success',
        message: `✅ Эндпоинт существует! Статус: ${response.status}`,
        details: response.data,
      });
    } catch (error: any) {
      // 401/403/400 означает что endpoint существует, просто неправильные данные
      if (error.response?.status === 401 || error.response?.status === 403 || error.response?.status === 400) {
        diagnostics.push({
          test: `POST ${API_ENDPOINTS.LOGIN}`,
          status: 'success',
          message: `✅ Эндпоинт найден! (${error.response.status} - ожидаемо для тестовых данных)`,
          details: error.response?.data,
        });
      } else if (error.response?.status === 404) {
        diagnostics.push({
          test: `POST ${API_ENDPOINTS.LOGIN}`,
          status: 'error',
          message: `❌ 404 - Эндпоинт не найден! Проверьте путь на backend.`,
          details: {
            currentPath: API_ENDPOINTS.LOGIN,
            suggestion: 'Попробуйте: /api/login, /login, /auth/login',
            responseData: error.response?.data,
          },
        });
      } else {
        diagnostics.push({
          test: `POST ${API_ENDPOINTS.LOGIN}`,
          status: 'error',
          message: `❌ Ошибка: ${error.code || error.message}`,
          details: error.response?.data,
        });
      }
    }

    // Тест 3: Проверка с прямым fetch
    console.log('🧪 Test 3: Direct fetch test');
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.HEALTH}`, {
        method: 'GET',
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      });
      
      if (response.ok) {
        const data = await response.json().catch(() => response.text());
        diagnostics.push({
          test: 'Direct Fetch (Health)',
          status: 'success',
          message: `✅ Fetch работает! Статус: ${response.status}`,
          details: data,
        });
      } else {
        diagnostics.push({
          test: 'Direct Fetch (Health)',
          status: 'error',
          message: `❌ Ошибка: HTTP ${response.status}`,
          details: await response.text(),
        });
      }
    } catch (error: any) {
      diagnostics.push({
        test: 'Direct Fetch (Health)',
        status: 'error',
        message: `❌ Fetch ошибка: ${error.message}`,
        details: error,
      });
    }

    setResults(diagnostics);
    setIsRunning(false);
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-gray-900">🔧 Диагностика Backend</h2>
        <Button
          onClick={runDiagnostics}
          disabled={isRunning}
          variant="outline"
          size="sm"
        >
          {isRunning ? '⏳ Проверка...' : '▶️ Запустить тесты'}
        </Button>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((result, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${
                result.status === 'success'
                  ? 'bg-green-50 border-green-200'
                  : result.status === 'error'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-lg">
                  {result.status === 'success' ? '✅' : '❌'}
                </span>
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-gray-700">
                    <strong>{result.test}</strong>
                  </p>
                  <p className="text-sm text-gray-600">{result.message}</p>
                  {result.details && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 cursor-pointer">
                        Показать детали
                      </summary>
                      <pre className="mt-2 text-xs bg-white p-2 rounded border border-gray-200 overflow-auto">
                        {JSON.stringify(result.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2 text-sm">
        <p className="text-blue-900">
          <strong>💡 Что делать при ошибках:</strong>
        </p>
        <ul className="text-blue-800 space-y-1 ml-4 list-disc">
          <li>
            <strong>ERR_NETWORK или CORS:</strong> Настройте CORS на backend
            (allow_origins=["*"])
          </li>
          <li>
            <strong>404 Not Found:</strong> Проверьте, что эндпоинт существует на
            backend
          </li>
          <li>
            <strong>Timeout:</strong> Убедитесь, что backend запущен и туннель
            активен
          </li>
          <li>
            <strong>Все тесты провалились:</strong> Backend вероятно не работает
            или URL туннеля неверен
          </li>
        </ul>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs space-y-1">
        <p className="text-gray-700">
          <strong>Конфигурация:</strong>
        </p>
        <p className="text-gray-600 font-mono">
          Base URL: https://get-anki.fan.ngrok.app/api/
        </p>
        <p className="text-gray-600 font-mono">
          Timeout: 30000ms
        </p>
        <p className="text-gray-600 font-mono">
          Headers: ngrok-skip-browser-warning: true
        </p>
      </div>
    </Card>
  );
}