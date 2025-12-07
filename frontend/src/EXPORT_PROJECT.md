# 📦 Как забрать фронтенд из Figma Make

## 🎯 Что вам нужно

Вы хотите взять весь код фронтенда и работать с ним в своей среде разработки (VSCode, WebStorm и т.д.).

---

## 📥 Способ 1: Экспорт через интерфейс Figma Make

### В интерфейсе Figma Make:

1. **Найдите кнопку экспорта** (обычно в правом верхнем углу)
   - Ищите иконку "Download" / "Export" / "⬇️"
   - Или меню "File" → "Export project"

2. **Скачайте ZIP архив** с проектом

3. **Распакуйте** на своём компьютере:
   ```bash
   unzip anki-generator-frontend.zip
   cd anki-generator-frontend
   ```

---

## 📥 Способ 2: Если нет кнопки экспорта

Если Figma Make не предоставляет прямого экспорта, вам нужно **скопировать все файлы вручную**.

### Список всех файлов проекта:

#### 📁 Корневая структура

```
/
├── App.tsx                          # Главный компонент
├── package.json                     # Зависимости (создать!)
├── tsconfig.json                    # TypeScript конфиг (создать!)
├── vite.config.ts                   # Vite конфиг (создать!)
├── index.html                       # HTML точка входа (создать!)
├── .env.production                  # Production переменные ✅
│
├── components/                      # Все компоненты
│   ├── AddWordForm.tsx
│   ├── AudioPlayer.tsx
│   ├── AvatarUpload.tsx
│   ├── BackendDiagnostics.tsx
│   ├── CreateDeckModal.tsx
│   ├── DeckCard.tsx
│   ├── DeleteDeckModal.tsx
│   ├── EditableText.tsx
│   ├── EditableTitle.tsx
│   ├── GeminiModelSelector.tsx
│   ├── GeneratedWordsGrid.tsx
│   ├── GenerationProgress.tsx
│   ├── GenerationSuccess.tsx
│   ├── Header.tsx
│   ├── ImagePreviewModal.tsx
│   ├── ImageProviderDropdown.tsx
│   ├── ImageProviderSelector.tsx
│   ├── ImageStyleSelector.tsx
│   ├── InsufficientTokensModal.tsx
│   ├── LanguageSelector.tsx
│   ├── Layout.tsx
│   ├── MediaModelSelector.tsx
│   ├── MediaSettings.tsx
│   ├── NetworkErrorBanner.tsx
│   ├── ProtectedRoute.tsx
│   ├── SmartWordInput.tsx
│   ├── TokenBalanceWidget.tsx
│   ├── TranslationTable.tsx
│   ├── WordCard.tsx
│   ├── WordChipsInput.tsx
│   ├── WordInput.tsx
│   ├── WordsTable.tsx
│   ├── figma/
│   │   └── ImageWithFallback.tsx
│   └── ui/                         # Все UI компоненты (shadcn/ui)
│       ├── accordion.tsx
│       ├── alert-dialog.tsx
│       ├── alert.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── checkbox.tsx
│       ├── dialog.tsx
│       ├── drawer.tsx
│       ├── dropdown-menu.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── popover.tsx
│       ├── progress.tsx
│       ├── select.tsx
│       ├── separator.tsx
│       ├── sheet.tsx
│       ├── slider.tsx
│       ├── sonner.tsx
│       ├── switch.tsx
│       ├── tabs.tsx
│       ├── textarea.tsx
│       ├── tooltip.tsx
│       └── ... (остальные UI компоненты)
│
├── contexts/                       # React контексты
│   ├── AuthContext.tsx
│   ├── LanguageContext.tsx
│   ├── ThemeContext.tsx
│   └── TokenContext.tsx
│
├── hooks/                          # Custom hooks
│   └── useAuth.ts
│
├── lib/                           # Утилиты и конфиг
│   ├── api-helpers.ts
│   ├── api.ts
│   ├── config.ts                  # ✅ Обновлён
│   └── utils.ts
│
├── locales/                       # Переводы (7 языков)
│   ├── de.ts
│   ├── en.ts
│   ├── es.ts
│   ├── fr.ts
│   ├── index.ts
│   ├── it.ts
│   ├── pt.ts
│   └── ru.ts
│
├── pages/                         # Страницы
│   ├── DeckEditorPage.tsx
│   ├── DecksPage.tsx
│   ├── LoginPage.tsx
│   ├── MainPage.tsx
│   ├── NotFoundPage.tsx
│   ├── ProfilePage.tsx
│   └── RegisterPage.tsx
│
├── services/                      # API сервисы
│   ├── api.ts
│   ├── auth.service.ts
│   ├── authService.ts
│   ├── deck.service.ts
│   ├── deckService.ts
│   ├── profile.service.ts
│   └── token.service.ts
│
├── styles/                        # Стили
│   └── globals.css
│
├── types/                         # TypeScript типы
│   └── index.ts
│
└── utils/                         # Вспомогательные функции
    ├── constants.ts
    ├── helpers.ts
    ├── language-helpers.ts
    ├── toast-helpers.ts
    ├── token-formatting.ts
    ├── token-helpers.ts
    └── url-helpers.ts
```

---

## 📝 Создайте конфигурационные файлы

После копирования файлов, создайте эти конфиги:

### 1. `package.json`

```json
{
  "name": "anki-generator-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.22.0",
    "lucide-react": "^0.344.0",
    "sonner": "^1.4.3",
    "recharts": "^2.12.0",
    "react-hook-form": "^7.55.0",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.4.2",
    "vite": "^5.1.6",
    "tailwindcss": "^4.0.0",
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.35"
  }
}
```

### 2. `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
});
```

### 3. `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path mapping */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["**/*.ts", "**/*.tsx"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 4. `tsconfig.node.json`

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

### 5. `index.html` (корень проекта)

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Anki Generator</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/main.tsx"></script>
  </body>
</html>
```

### 6. `main.tsx` (корень проекта)

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

### 7. `.gitignore`

```
# Dependencies
node_modules/

# Build output
dist/
build/

# Environment variables
.env
.env.local
.env.development
# .env.production - можно закоммитить

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
```

---

## 🚀 Установка и запуск

После того как скопировали все файлы и создали конфиги:

```bash
# 1. Установите зависимости
npm install

# 2. Запустите в режиме разработки
npm run dev

# Приложение откроется на http://localhost:3000
```

---

## 📦 Сборка для продакшена

Когда будете готовы к деплою на Django:

```bash
# Соберите production билд
npm run build

# Это создаст папку dist/ с оптимизированными файлами
```

Затем следуйте инструкциям из **QUICK_DEPLOY.md** для копирования в Django.

---

## ⚙️ Настройка API URL

### Для разработки (ngrok)

В файле `/lib/config.ts` уже настроено:

```typescript
export const API_BASE_URL = 
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) 
  || 'https://get-anki.fan.ngrok.app';
```

### Для продакшена (Django на том же домене)

Создан файл `.env.production`:

```bash
VITE_API_BASE_URL=/api
```

При запуске `npm run build` автоматически используется эта переменная.

---

## ✅ Проверка

После установки проверьте, что всё работает:

```bash
# Запустите dev сервер
npm run dev

# Откройте http://localhost:3000
# Должно загрузиться приложение и подключиться к ngrok бэкенду
```

---

## 📋 Чеклист экспорта

- [ ] Скопированы все файлы из директорий:
  - [ ] `/components` (все .tsx файлы)
  - [ ] `/contexts` (4 файла)
  - [ ] `/hooks` (1 файл)
  - [ ] `/lib` (4 файла)
  - [ ] `/locales` (8 файлов)
  - [ ] `/pages` (7 файлов)
  - [ ] `/services` (7 файлов)
  - [ ] `/styles` (1 файл)
  - [ ] `/types` (1 файл)
  - [ ] `/utils` (7 файлов)
  - [ ] `App.tsx`
  - [ ] `.env.production`

- [ ] Созданы конфигурационные файлы:
  - [ ] `package.json`
  - [ ] `vite.config.ts`
  - [ ] `tsconfig.json`
  - [ ] `tsconfig.node.json`
  - [ ] `index.html`
  - [ ] `main.tsx`
  - [ ] `.gitignore`

- [ ] Установлены зависимости: `npm install`
- [ ] Приложение запускается: `npm run dev`
- [ ] Сборка работает: `npm run build`

---

## 💡 Готовый шаблон команд

```bash
# Создайте папку проекта
mkdir anki-generator-frontend
cd anki-generator-frontend

# Создайте структуру папок
mkdir -p components/ui components/figma
mkdir -p contexts hooks lib locales pages services styles types utils

# Скопируйте все файлы из Figma Make в соответствующие папки
# (используйте интерфейс Figma Make или копируйте вручную)

# Создайте конфигурационные файлы
# (скопируйте содержимое из этого гайда)

# Установите зависимости
npm install

# Запустите
npm run dev
```

---

**Готово! Теперь у вас полноценный React проект, который можно развивать локально.** 🚀
