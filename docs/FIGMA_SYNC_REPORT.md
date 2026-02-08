# Отчет о различиях между Figma репозиторием и текущим фронтендом

**Дата анализа:** 2026-01-11 18:38:33
**Figma репозиторий:** https://github.com/Prygunov-Andrei/Ankiflashcardgenerator.git

## ⚠️ ВАЖНО

Этот отчет показывает, какие файлы/изменения есть в **текущем репозитории**, но отсутствуют в **Figma репозитории**.

**Направление синхронизации:** Текущий репозиторий → Figma (вручную)

---

## 📊 Сводка

- **Новых файлов** (только в текущем): 7
- **Измененных файлов**: 25
- **Файлов только в Figma** (для справки): 0

---

## 📁 Новые файлы (нужно добавить в Figma)

Эти файлы есть в текущем репозитории, но отсутствуют в Figma репозитории.

**Действие:** Скопировать эти файлы в Figma вручную.


```
Dockerfile
public/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png
public/8438de77d51aa44238d74565f4aecffecf7eb633.png
package-lock.json
nginx.conf
.env.development
src/components/ImageEditModal.tsx
```

---

## ✏️ Измененные файлы (нужно обновить в Figma)

Эти файлы существуют в обоих репозиториях, но имеют различия.

**Действие:** Обновить содержимое этих файлов в  Figma вручную.


```
package.json
src/types/index.ts
src/contexts/ThemeContext.tsx
src/locales/de.ts
src/locales/it.ts
src/locales/es.ts
src/locales/en.ts
src/locales/fr.ts
src/locales/ru.ts
src/locales/pt.ts
src/locales/index.ts
src/utils/url-helpers.ts
src/components/WordCard.tsx
src/components/WordsTable.tsx
src/components/DeckCard.tsx
src/components/Header.tsx
src/components/InvertWordsConfirmModal.tsx
src/lib/config.ts
src/pages/RegisterPage.tsx
src/pages/LoginPage.tsx
src/pages/DeckEditorPage.tsx
src/pages/MainPage.tsx
src/pages/DecksPage.tsx
src/services/deck.service.ts
src/services/api.ts
```

### Детали изменений


### package.json
```diff
--- /tmp/figma-diff-analysis/figma-repo/package.json	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/package.json	2025-12-15 14:57:18
@@ -51,8 +51,10 @@
           "vaul": "^1.1.2"
       },
       "devDependencies": {
+          "@tailwindcss/postcss": "^4.0.0",
           "@types/node": "^20.10.0",
           "@vitejs/plugin-react-swc": "^3.10.2",
+          "autoprefixer": "^10.4.20",
           "vite": "6.3.5"
       },
       "scripts": {
```

### src/types/index.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/types/index.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/types/index.ts	2026-01-11 17:52:54
@@ -22,15 +22,172 @@
 
 // ========== WORD ==========
 
+export type LearningStatus = 'new' | 'learning' | 'reviewing' | 'mastered';
+
+export type PartOfSpeech = 
+  | 'noun' 
+  | 'verb' 
+  | 'adjective' 
+  | 'adverb' 
+  | 'pronoun' 
+  | 'preposition' 
+  | 'conjunction' 
+  | 'interjection' 
+  | 'article' 
+  | 'numeral' 
+  | 'particle' 
+  | 'other';
+
+export interface WordSentence {
+  text: string;
+  source: 'ai' | 'user';
+}
+
 export interface Word {
   id: number;
   original_word: string;
   translation: string;
   language: string;
+  card_type?: 'normal' | 'inverted' | 'empty'; // deprecated
   audio_file: string | null;
   image_file: string | null;
+  
+  // Новые поля
+  etymology: string;
+  sentences: WordSentence[];
+  notes: string;
+  hint_text: string;
+  hint_audio: string | null;
+  part_of_speech: PartOfSpeech | '';
+  stickers: string[];  // ["❤️", "⭐"]
+  learning_status: LearningStatus;
+  
+  created_at: string;
+  updated_at: string;
 }
 
```

### src/contexts/ThemeContext.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/contexts/ThemeContext.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/contexts/ThemeContext.tsx	2025-12-12 16:38:31
@@ -6,6 +6,7 @@
 
 interface ThemeContextType {
   theme: Theme;
+  isDark: boolean;
   toggleTheme: () => void;
   setTheme: (theme: Theme) => void;
 }
@@ -24,7 +25,8 @@
   children: ReactNode;
 }
 
-const API_BASE_URL = 'https://get-anki.fan.ngrok.app/api';
+// API URL из переменной окружения или пустая строка для продакшена
+const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.startsWith('/') ? '' : (import.meta.env.VITE_API_BASE_URL || '');
 
 export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
   const authContext = useAuthContext();
@@ -113,6 +115,7 @@
 
   const value = {
     theme,
+    isDark: theme === 'dark',
     toggleTheme,
     setTheme,
   };
```

### src/locales/de.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/de.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/de.ts	2026-01-02 17:42:17
@@ -119,6 +119,9 @@
     words: 'Wörter',
     word: 'Wort',
     wordsTwo: 'Wörter',
+    cards: 'Karten',
+    card: 'Karte',
+    cardsTwo: 'Karten',
     wordsCount: 'Anzahl der Wörter',
     noDeck: 'Noch keine Decks',
     createFirstDeck: 'Erstellen Sie Ihr erstes Deck',
@@ -147,6 +150,7 @@
     addWordBeforeGeneration: 'Fügen Sie mindestens ein Wort vor der Generierung hinzu',
     goToMainPage: 'Gehen Sie zur Hauptseite, um ein Deck mit KI-generierten ANKI-Karten zu erstellen',
     updated: 'Aktualisiert',
+    created: 'Erstellt',
     recently: 'kürzlich',
     // Deck-Editor
     backToDecks: 'Zurück zu Decks',
@@ -244,9 +248,12 @@
     editTranslationsHint: '💡 Sie können Übersetzungen bearbeiten oder unnötige Wörter entfernen',
     regenerate: 'Neu generieren',
     regenerateImage: 'Bild',
+    editImage: 'Bild bearbeiten',
+    editImageHint: 'Beschreiben Sie, was hinzugefügt oder geändert werden soll',
+    editImagePlaceholder: 'füge ein Pferd und Reiter hinzu',
+    editImageButton: 'Bearbeiten',
     regenerateAudio: 'Audio',
     delete: 'Löschen',
-    deleteWord: 'Wort',
     deleteImage: 'Bild',
     deleteAudio: 'Audio',
     moveToDeck: 'Zu Deck verschieben',
@@ -255,6 +262,16 @@
     invertWordConfirm: 'Umgekehrte Karte erstellen',
     invertAllWordsConfirm: 'Umgekehrte Karten für alle Wörter erstellen?',
     invertAllWordsWarning: 'Dies erstellt umgekehrte Karten für jedes Wort im Deck. Das Deck wird sich verdoppeln.',
+    // Kartentypen
+    cardType: 'Kartentyp',
+    cardTypeNormal: 'Normal',
+    cardTypeInverted: 'Invertiert',
+    cardTypeEmpty: 'Leer',
+    // Filter
+    filterAll: 'Alle',
+    filterNormal: 'Normal',
+    filterInverted: 'Invertiert',
+    filterEmpty: 'Leer',
     invertingWord: 'Invertierung...',
     invertingAllWords: 'Alle Wörter invertieren...',
```

### src/locales/it.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/it.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/it.ts	2026-01-02 17:42:55
@@ -100,6 +100,9 @@
     words: 'parole',
     word: 'parola',
     wordsTwo: 'parole',
+    cards: 'carte',
+    card: 'carta',
+    cardsTwo: 'carte',
     wordsCount: 'Numero di parole',
     noDeck: 'Nessun mazzo ancora',
     createFirstDeck: 'Crea il tuo primo mazzo',
@@ -128,6 +131,7 @@
     addWordBeforeGeneration: 'Aggiungi almeno una parola prima della generazione',
     goToMainPage: 'Vai alla pagina principale per creare un mazzo con carte ANKI generate dall\'IA',
     updated: 'Aggiornato',
+    created: 'Creato',
     recently: 'recentemente',
     backToDecks: 'Torna ai mazzi',
     deckNamePlaceholder: 'Nome del mazzo',
@@ -223,9 +227,12 @@
     editTranslationsHint: '💡 Puoi modificare le traduzioni o rimuovere le parole non necessarie',
     regenerate: 'Rigenera',
     regenerateImage: 'Immagine',
+    editImage: 'Modifica immagine',
+    editImageHint: 'Descrivi cosa aggiungere o modificare',
+    editImagePlaceholder: 'aggiungi un cavallo e cavaliere',
+    editImageButton: 'Modifica',
     regenerateAudio: 'Audio',
     delete: 'Elimina',
-    deleteWord: 'Parola',
     deleteImage: 'Immagine',
     deleteAudio: 'Audio',
     moveToDeck: 'Sposta nel mazzo',
@@ -234,6 +241,16 @@
     invertWordConfirm: 'Crea scheda inversa',
     invertAllWordsConfirm: 'Creare schede inverse per tutte le parole?',
     invertAllWordsWarning: 'Questo creerà schede inverse per ogni parola nel mazzo. Il mazzo raddoppierà.',
+    // Tipi di scheda
+    cardType: 'Tipo di scheda',
+    cardTypeNormal: 'Normale',
+    cardTypeInverted: 'Invertita',
+    cardTypeEmpty: 'Vuota',
+    // Filtri
+    filterAll: 'Tutte',
+    filterNormal: 'Normali',
+    filterInverted: 'Invertite',
+    filterEmpty: 'Vuote',
     invertingWord: 'Inversione...',
     invertingAllWords: 'Inversione di tutte le parole...',
```

### src/locales/es.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/es.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/es.ts	2026-01-02 17:42:50
@@ -100,6 +100,9 @@
     words: 'palabras',
     word: 'palabra',
     wordsTwo: 'palabras',
+    cards: 'tarjetas',
+    card: 'tarjeta',
+    cardsTwo: 'tarjetas',
     wordsCount: 'Número de palabras',
     noDeck: 'Aún no hay mazos',
     createFirstDeck: 'Crea tu primer mazo',
@@ -128,6 +131,7 @@
     addWordBeforeGeneration: 'Agregue al menos una palabra antes de generar',
     goToMainPage: 'Vaya a la página principal para crear un mazo con tarjetas ANKI generadas por IA',
     updated: 'Actualizado',
+    created: 'Creado',
     recently: 'recientemente',
     backToDecks: 'Volver a mazos',
     deckNamePlaceholder: 'Nombre del mazo',
@@ -223,9 +227,12 @@
     editTranslationsHint: '💡 Puede editar traducciones o eliminar palabras innecesarias',
     regenerate: 'Regenerar',
     regenerateImage: 'Imagen',
+    editImage: 'Editar imagen',
+    editImageHint: 'Describe qué añadir o cambiar',
+    editImagePlaceholder: 'añade un caballo y jinete',
+    editImageButton: 'Editar',
     regenerateAudio: 'Audio',
     delete: 'Eliminar',
-    deleteWord: 'Palabra',
     deleteImage: 'Imagen',
     deleteAudio: 'Audio',
     moveToDeck: 'Mover al mazo',
@@ -234,6 +241,16 @@
     invertWordConfirm: 'Crear tarjeta inversa',
     invertAllWordsConfirm: '¿Crear tarjetas inversas para todas las palabras?',
     invertAllWordsWarning: 'Esto creará tarjetas inversas para cada palabra del mazo. El mazo se duplicará.',
+    // Tipos de tarjeta
+    cardType: 'Tipo de tarjeta',
+    cardTypeNormal: 'Normal',
+    cardTypeInverted: 'Invertida',
+    cardTypeEmpty: 'Vacía',
+    // Filtros
+    filterAll: 'Todas',
+    filterNormal: 'Normal',
+    filterInverted: 'Invertidas',
+    filterEmpty: 'Vacías',
     invertingWord: 'Invirtiendo...',
     invertingAllWords: 'Invirtiendo todas las palabras...',
```

### src/locales/en.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/en.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/en.ts	2026-01-02 17:42:47
@@ -119,6 +119,9 @@
     words: 'words',
     word: 'word',
     wordsTwo: 'words',
+    cards: 'cards',
+    card: 'card',
+    cardsTwo: 'cards',
     wordsCount: 'Words count',
     noDeck: 'No decks yet',
     createFirstDeck: 'Create your first deck',
@@ -147,6 +150,7 @@
     addWordBeforeGeneration: 'Add at least one word before generation',
     goToMainPage: 'Go to the main page to create a deck with AI-generated ANKI cards',
     updated: 'Updated',
+    created: 'Created',
     recently: 'recently',
     // Deck editor
     backToDecks: 'Back to decks',
@@ -242,9 +246,12 @@
     editTranslationsHint: '💡 You can edit translations or remove unnecessary words',
     regenerate: 'Regenerate',
     regenerateImage: 'Image',
+    editImage: 'Edit image',
+    editImageHint: 'Describe what to add or change',
+    editImagePlaceholder: 'add a horse and rider',
+    editImageButton: 'Edit',
     regenerateAudio: 'Audio',
     delete: 'Delete',
-    deleteWord: 'Word',
     deleteImage: 'Image',
     deleteAudio: 'Audio',
     moveToDeck: 'Move to deck',
@@ -254,6 +261,16 @@
     invertAllWordsConfirm: 'Create reverse cards for all words?',
     invertAllWordsWarning: 'This will create reverse cards for each word in the deck. The deck will double in size.',
     invertWordWarning: 'This will create a reverse card for this word. The word and translation will be swapped.',
+    // Card types
+    cardType: 'Card type',
+    cardTypeNormal: 'Normal',
+    cardTypeInverted: 'Inverted',
+    cardTypeEmpty: 'Empty',
+    // Filters
+    filterAll: 'All',
+    filterNormal: 'Normal',
+    filterInverted: 'Inverted',
+    filterEmpty: 'Empty',
     invertingWord: 'Inverting...',
     invertingAllWords: 'Inverting all words...',
```

### src/locales/fr.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/fr.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/fr.ts	2026-01-02 17:42:55
@@ -112,6 +112,9 @@
     words: 'mots',
     word: 'mot',
     wordsTwo: 'mots',
+    cards: 'cartes',
+    card: 'carte',
+    cardsTwo: 'cartes',
     wordsCount: 'Nombre de mots',
     noDeck: 'Pas encore de paquets',
     createFirstDeck: 'Créez votre premier paquet',
@@ -140,6 +143,7 @@
     addWordBeforeGeneration: 'Ajoutez au moins un mot avant la génération',
     goToMainPage: 'Allez à la page principale pour créer un paquet avec des cartes ANKI générées par IA',
     updated: 'Mis à jour',
+    created: 'Créé',
     recently: 'récemment',
     backToDecks: 'Retour aux paquets',
     deckNamePlaceholder: 'Nom du paquet',
@@ -235,9 +239,12 @@
     editTranslationsHint: '💡 Vous pouvez modifier les traductions ou supprimer les mots inutiles',
     regenerate: 'Régénérer',
     regenerateImage: 'Image',
+    editImage: 'Modifier l\'image',
+    editImageHint: 'Décrivez ce qu\'il faut ajouter ou modifier',
+    editImagePlaceholder: 'ajouter un cheval et un cavalier',
+    editImageButton: 'Modifier',
     regenerateAudio: 'Audio',
     delete: 'Supprimer',
-    deleteWord: 'Mot',
     deleteImage: 'Image',
     deleteAudio: 'Audio',
     moveToDeck: 'Déplacer vers le paquet',
@@ -246,6 +253,16 @@
     invertWordConfirm: 'Créer une carte inversée',
     invertAllWordsConfirm: 'Créer des cartes inversées pour tous les mots?',
     invertAllWordsWarning: 'Cela créera des cartes inversées pour chaque mot du paquet. La taille du paquet doublera.',
+    // Types de carte
+    cardType: 'Type de carte',
+    cardTypeNormal: 'Normale',
+    cardTypeInverted: 'Inversée',
+    cardTypeEmpty: 'Vide',
+    // Filtres
+    filterAll: 'Toutes',
+    filterNormal: 'Normales',
+    filterInverted: 'Inversées',
+    filterEmpty: 'Vides',
     invertingWord: 'Inversion...',
     invertingAllWords: 'Inversion de tous les mots...',
```

### src/locales/ru.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/ru.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/ru.ts	2026-01-02 17:42:03
@@ -117,6 +117,9 @@
     words: 'слов',
     word: 'слово',
     wordsTwo: 'слова',
+    cards: 'карточек',
+    card: 'карточка',
+    cardsTwo: 'карточки',
     wordsCount: 'Количество слов',
     noDeck: 'Колод пока нет',
     createFirstDeck: 'Создайте свою первую колоду',
@@ -145,6 +148,7 @@
     addWordBeforeGeneration: 'Добавьте хотя бы одно слово перед генерацией',
     goToMainPage: 'Перейдите на главную страницу, чтобы создать колоду с AI-генерацией карточек ANKI',
     updated: 'Обновлено',
+    created: 'Создано',
     recently: 'недавно',
     // Редактор колоды
     backToDecks: 'Вернуться к колодам',
@@ -246,8 +250,11 @@
     regenerate: 'Перегенерировать',
     regenerateImage: 'Изображение',
     regenerateAudio: 'Аудио',
+    editImage: 'Изменить картинку',
+    editImageHint: 'Опишите что добавить или изменить',
+    editImagePlaceholder: 'добавь коня и всадника',
+    editImageButton: 'Изменить',
     delete: 'Удалить',
-    deleteWord: 'Слово',
     deleteImage: 'Изображение',
     deleteAudio: 'Аудио',
     moveToDeck: 'Переместить в колоду',
@@ -257,6 +264,16 @@
     invertAllWordsConfirm: 'Создать обратные карточки для всех слов?',
     invertAllWordsWarning: 'Это создаст обратные карточки для каждого слова в колоде. Размер колоды удвоится.',
     invertWordWarning: 'Это создаст обратную карточку для этого слова. Слово и перевод поменяются местами.',
+    // Типы карточек
+    cardType: 'Тип карточки',
+    cardTypeNormal: 'Обычная',
+    cardTypeInverted: 'Инвертированная',
+    cardTypeEmpty: 'Пустая',
+    // Фильтры
+    filterAll: 'Все',
+    filterNormal: 'Обычные',
+    filterInverted: 'Инвертированные',
+    filterEmpty: 'Пустые',
     invertingWord: 'Инвертирование...',
     invertingAllWords: 'Инвертирование всех слов...',
     wordInverted: 'Слово инвертировано',
```

### src/locales/pt.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/pt.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/pt.ts	2026-01-02 17:42:59
@@ -113,6 +113,9 @@
     words: 'palavras',
     word: 'palavra',
     wordsTwo: 'palavras',
+    cards: 'cartões',
+    card: 'cartão',
+    cardsTwo: 'cartões',
     wordsCount: 'Número de palavras',
     noDeck: 'Ainda não há baralhos',
     createFirstDeck: 'Crie seu primeiro baralho',
@@ -141,6 +144,7 @@
     addWordBeforeGeneration: 'Adicione pelo menos uma palavra antes da geração',
     goToMainPage: 'Vá para a página principal para criar um baralho com cartões ANKI gerados por IA',
     updated: 'Atualizado',
+    created: 'Criado',
     recently: 'recentemente',
     backToDecks: 'Voltar aos baralhos',
     deckNamePlaceholder: 'Nome do baralho',
@@ -232,9 +236,12 @@
     editTranslationsHint: '💡 Você pode editar traduções ou remover palavras desnecessárias',
     regenerate: 'Regenerar',
     regenerateImage: 'Imagem',
+    editImage: 'Editar imagem',
+    editImageHint: 'Descreva o que adicionar ou alterar',
+    editImagePlaceholder: 'adicione um cavalo e cavaleiro',
+    editImageButton: 'Editar',
     regenerateAudio: 'Áudio',
     delete: 'Excluir',
-    deleteWord: 'Palavra',
     deleteImage: 'Imagem',
     deleteAudio: 'Áudio',
     moveToDeck: 'Mover para o baralho',
@@ -243,6 +250,16 @@
     invertWordConfirm: 'Criar cartão inverso',
     invertAllWordsConfirm: 'Criar cartões inversos para todas as palavras?',
     invertAllWordsWarning: 'Isso criará cartões inversos para cada palavra do baralho. O baralho dobrará de tamanho.',
+    // Tipos de cartão
+    cardType: 'Tipo de cartão',
+    cardTypeNormal: 'Normal',
+    cardTypeInverted: 'Invertido',
+    cardTypeEmpty: 'Vazio',
+    // Filtros
+    filterAll: 'Todos',
+    filterNormal: 'Normal',
+    filterInverted: 'Invertido',
+    filterEmpty: 'Vazio',
     invertingWord: 'Invertendo...',
     invertingAllWords: 'Invertendo todas as palavras...',
```

### src/locales/index.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/locales/index.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/locales/index.ts	2026-01-01 17:01:05
@@ -1,4 +1,5 @@
-import { ru, TranslationKeys } from './ru';
+import { ru } from './ru';
+import type { TranslationKeys } from './ru';
 import { en } from './en';
 import { pt } from './pt';
 import { de } from './de';
@@ -32,4 +33,4 @@
 
 export type SupportedLocale = keyof typeof translations;
 
-export { TranslationKeys } from './ru';
\ No newline at end of file
+export type { TranslationKeys } from './ru';
\ No newline at end of file
```

### src/utils/url-helpers.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/utils/url-helpers.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/utils/url-helpers.ts	2025-12-12 16:38:31
@@ -1,9 +1,10 @@
 /**
- * Base URL backend API (через ngrok - постоянный домен)
+ * Base URL backend API
+ * В продакшене: пустая строка (запросы на тот же домен)
+ * В разработке: ngrok URL из .env.development
  */
+const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.startsWith('/') ? '' : (import.meta.env.VITE_API_BASE_URL || '');
 
-const API_BASE_URL = 'https://get-anki.fan.ngrok.app';
-
 /**
  * Преобразует относительный URL в абсолютный
  * Django часто возвращает относительные пути для медиа-файлов
```

### src/components/WordCard.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/components/WordCard.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/components/WordCard.tsx	2026-01-02 17:49:05
@@ -4,8 +4,9 @@
 import { Badge } from './ui/badge';
 import { AudioPlayer } from './AudioPlayer';
 import { ImagePreviewModal } from './ImagePreviewModal';
+import { ImageEditModal } from './ImageEditModal';
 import { EditableText } from './EditableText';
-import { Trash2, RefreshCw, ImageIcon, MoreVertical, ArrowRight, Volume2, ArrowLeftRight, FileText } from 'lucide-react';
+import { Trash2, RefreshCw, ImageIcon, MoreVertical, ArrowRight, Volume2, ArrowLeftRight, FileText, Wand2, BookOpen } from 'lucide-react';
 import {
   DropdownMenu,
   DropdownMenuContent,
@@ -25,9 +26,11 @@
   audioUrl?: string;
   wordId?: number;
   deckId?: number;
+  cardType?: 'normal' | 'inverted' | 'empty';
   onDelete?: () => void;
   onRegenerateImage?: () => Promise<void>;
   onRegenerateAudio?: () => Promise<void>;
+  onEditImage?: (mixin: string) => Promise<void>;
   onDeleteImage?: () => Promise<void>;
   onDeleteAudio?: () => Promise<void>;
   onMoveToDeck?: (deckId: number, deckName: string) => Promise<void>;
@@ -51,9 +54,11 @@
   audioUrl,
   wordId,
   deckId,
+  cardType = 'normal',
   onDelete,
   onRegenerateImage,
   onRegenerateAudio,
+  onEditImage,
   onDeleteImage,
   onDeleteAudio,
   onMoveToDeck,
@@ -73,6 +78,7 @@
   } | null>(null);
   const [regeneratingImage, setRegeneratingImage] = useState(false);
   const [regeneratingAudio, setRegeneratingAudio] = useState(false);
+  const [editImageModalOpen, setEditImageModalOpen] = useState(false);
 
   // Фильтруем список колод - используем availableDecks если передан, иначе allDecks (все колоды минус текущую будут показаны)
   const decksToShow = availableDecks || allDecks;
@@ -112,9 +118,60 @@
     }
   };
 
+  /**
```

### src/components/WordsTable.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/components/WordsTable.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/components/WordsTable.tsx	2026-01-02 17:01:46
@@ -1,8 +1,9 @@
-import React, { useState } from 'react';
+import React, { useState, useMemo } from 'react';
 import { Word, Deck } from '../types';
 import { Button } from './ui/button';
 import { WordCard } from './WordCard';
-import { Loader2 } from 'lucide-react';
+import { Badge } from './ui/badge';
+import { Loader2, Filter } from 'lucide-react';
 import {
   AlertDialog,
   AlertDialogAction,
@@ -25,6 +26,7 @@
   onDeleteWord: (wordId: number) => Promise<void>;
   onRegenerateImage?: (wordId: number, word: string, translation: string) => Promise<void>;
   onRegenerateAudio?: (wordId: number, word: string) => Promise<void>;
+  onEditImage?: (wordId: number, mixin: string) => Promise<void>;
   onDeleteImage?: (wordId: number) => Promise<void>;
   onDeleteAudio?: (wordId: number) => Promise<void>;
   onMoveCardToDeck?: (wordId: number, toDeckId: number, toDeckName: string) => Promise<void>;
@@ -48,6 +50,7 @@
   onDeleteWord,
   onRegenerateImage,
   onRegenerateAudio,
+  onEditImage,
   onDeleteImage,
   onDeleteAudio,
   onMoveCardToDeck,
@@ -62,6 +65,7 @@
   const [deletingWordId, setDeletingWordId] = useState<number | null>(null);
   const [wordToDelete, setWordToDelete] = useState<Word | null>(null);
   const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
+  const [cardTypeFilter, setCardTypeFilter] = useState<'all' | 'normal' | 'inverted' | 'empty'>('all');
   const t = useTranslation();
 
   /**
@@ -73,6 +77,15 @@
   };
 
   /**
+   * Фильтрация слов по типу карточки
+   */
+  const filteredWords = useMemo(() => {
+    if (!words) return [];
+    if (cardTypeFilter === 'all') return words;
+    return words.filter((word) => word.card_type === cardTypeFilter);
+  }, [words, cardTypeFilter]);
+
```

### src/components/DeckCard.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/components/DeckCard.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/components/DeckCard.tsx	2026-01-02 17:46:03
@@ -81,6 +81,17 @@
     // Для других языков
     return count === 1 ? t.decks.word : t.decks.words;
   };
+  
+  // Плюрализация карточек
+  const getCardsText = (count: number) => {
+    if (locale === 'ru') {
+      if (count === 1) return t.decks.card;
+      if (count >= 2 && count <= 4) return t.decks.cardsTwo;
+      return t.decks.cards;
+    }
+    // Для других языков
+    return count === 1 ? t.decks.card : t.decks.cards;
+  };
 
   return (
     <Card className="group relative overflow-hidden transition-all hover:shadow-lg dark:hover:shadow-cyan-500/10">
@@ -195,18 +206,42 @@
 
           {/* Метаинформация */}
           <div className="space-y-2">
-            {/* Количество слов */}
+            {/* Количество слов и карточек */}
             <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
               <BookOpen className="mr-2 h-4 w-4 text-cyan-500" />
               <span>
-                {deck.words_count} {getWordsText(deck.words_count)}
+                {deck.unique_words_count !== undefined && deck.unique_words_count !== deck.words_count ? (
+                  <>
+                    {deck.unique_words_count} {getWordsText(deck.unique_words_count)} ({deck.words_count} {getCardsText(deck.words_count)})
+                  </>
+                ) : (
+                  <>
+                    {deck.words_count} {getWordsText(deck.words_count)}
+                  </>
+                )}
               </span>
             </div>
 
-            {/* Дата обновления */}
-            <div className="flex items-center text-sm text-gray-500 dark:text-gray-500">
-              <Calendar className="mr-2 h-4 w-4" />
-              <span>{t.decks.updated} {getRelativeTime(deck.updated_at)}</span>
+            {/* Дата создания и обновления */}
+            <div className="space-y-1">
+              {/* Дата создания */}
+              <div className="flex items-center text-sm text-gray-500 dark:text-gray-500">
```

### src/components/Header.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/components/Header.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/components/Header.tsx	2025-12-12 15:48:00
@@ -19,8 +19,9 @@
 import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from './ui/sheet';
 import { VisuallyHidden } from './ui/visually-hidden';
 import { TokenBalanceWidget } from './TokenBalanceWidget';
-import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
-import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';
+// Логотипы из папки public (абсолютные пути)
+const logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
+const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';
 
 /**
  * Компонент Header - шапка приложения с навигацией
```

### src/components/InvertWordsConfirmModal.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/components/InvertWordsConfirmModal.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/components/InvertWordsConfirmModal.tsx	2026-01-02 17:34:30
@@ -67,9 +67,62 @@
                 </span>
                 {deck && deck.words_count && (
                   <span className="block font-semibold text-gray-900 dark:text-gray-100">
-                    {t.decks.currentSize || 'Текущий размер'}: {deck.words_count} {deck.words_count === 1 ? t.decks.word : t.decks.words}
-                    <br />
-                    {t.decks.afterInvert || 'После инвертирования'}: {deck.words_count * 2} {t.decks.words}
+                    {(() => {
+                      // Подсчитываем количество обычных карточек, которые будут инвертированы
+                      // Важно: учитываем только те обычные слова, у которых еще нет инвертированной версии в колоде
+                      const words = deck.words || [];
+                      
+                      let normalWordsToInvert = 0;
+                      
+                      if (words.length > 0 && deck.source_lang && deck.target_lang) {
+                        // Фильтруем обычные слова
+                        const normalWords = words.filter((w: any) => w.card_type === 'normal' || !w.card_type);
+                        
+                        // Для каждого обычного слова проверяем, есть ли уже его инвертированная версия
+                        normalWordsToInvert = normalWords.filter((normalWord: any) => {
+                          // Инвертированная версия = слово, где:
+                          // - original_word == translation обычного слова
+                          // - translation == original_word обычного слова
+                          // - language == source_lang колоды
+                          const invertedOriginal = normalWord.translation;
+                          const invertedTranslation = normalWord.original_word;
+                          
+                          // Проверяем, есть ли такое слово в колоде
+                          const hasInvertedVersion = words.some((w: any) => 
+                            w.original_word === invertedOriginal &&
+                            w.translation === invertedTranslation &&
+                            w.language === deck.source_lang
+                          );
+                          
+                          return !hasInvertedVersion; // Инвертируем только если инвертированной версии нет
+                        }).length;
+                      } else if (words.length > 0) {
+                        // Если нет source_lang/target_lang, просто считаем все обычные слова
+                        normalWordsToInvert = words.filter((w: any) => w.card_type === 'normal' || !w.card_type).length;
+                      } else {
+                        // Если слов нет в массиве, предполагаем что все слова обычные
+                        normalWordsToInvert = deck.words_count;
+                      }
+                      
+                      const currentSize = deck.words_count;
+                      const afterInvert = currentSize + normalWordsToInvert; // Текущий размер + новые инвертированные
+                      
+                      return (
```

### src/lib/config.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/lib/config.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/lib/config.ts	2025-12-12 16:38:31
@@ -1,11 +1,31 @@
 /**
- * Base URL backend API (через ngrok - постоянный домен)
- * В продакшене используется относительный путь (тот же домен)
+ * Base URL backend API
+ * 
+ * Логика определения URL:
+ * - В продакшене (VITE_API_BASE_URL=/api): пустая строка (эндпоинты уже содержат /api)
+ * - В разработке: VITE_API_BASE_URL из .env.development или пустая строка
+ * 
+ * ВАЖНО: ngrok URL должен быть в .env.development, НЕ захардкожен в коде!
  */
-export const API_BASE_URL = 
-  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) 
-  || 'https://get-anki.fan.ngrok.app';
+const getApiBaseUrl = (): string => {
+  const envUrl = import.meta.env.VITE_API_BASE_URL;
+  
+  // Если задана переменная окружения
+  if (envUrl) {
+    // Если это относительный путь (/api), возвращаем пустую строку
+    // т.к. эндпоинты уже содержат /api
+    if (envUrl.startsWith('/')) {
+      return '';
+    }
+    return envUrl;
+  }
+  
+  // По умолчанию - пустая строка (для продакшена)
+  return '';
+};
 
+export const API_BASE_URL = getApiBaseUrl();
+
 /**
  * API эндпоинты приложения
  */
@@ -43,6 +63,9 @@
   timeout: 30000, // 30 секунд
   headers: {
     'Content-Type': 'application/json',
-    'ngrok-skip-browser-warning': 'true', // Для совместимости с различными туннелями
+    // Добавляем ngrok header только в разработке (не в продакшене)
+    ...(typeof import.meta !== 'undefined' && !import.meta.env?.PROD && {
+      'ngrok-skip-browser-warning': 'true',
+    }),
   },
 } as const;
```

### src/pages/RegisterPage.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/pages/RegisterPage.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/pages/RegisterPage.tsx	2025-12-12 15:48:00
@@ -9,8 +9,9 @@
 import authService from '../services/authService';
 import { showSuccess, showError } from '../utils/toast-helpers';
 import { LanguageSelector } from '../components/LanguageSelector';
-import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
-import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';
+// Логотипы из папки public (абсолютные пути)
+const logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
+const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';
 
 /**
  * Страница регистрации (всегда на английском языке)
@@ -29,7 +30,8 @@
   
   const { login } = useAuthContext();
   const navigate = useNavigate();
-  const { isDark } = useTheme();
+  const { theme } = useTheme();
+  const isDark = theme === 'dark';
 
   // Валидация формы
   const validateForm = (): boolean => {
```

### src/pages/LoginPage.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/pages/LoginPage.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/pages/LoginPage.tsx	2025-12-12 15:48:00
@@ -8,9 +8,11 @@
 import { useTheme } from '../contexts/ThemeContext';
 import authService from '../services/authService';
 import { showSuccess, showError } from '../utils/toast-helpers';
-import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
-import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';
 
+// Логотипы из папки public (абсолютные пути)
+const logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';
+const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';
+
 /**
  * Страница входа (всегда на английском языке)
  */
@@ -22,7 +24,8 @@
   
   const { login } = useAuthContext();
   const navigate = useNavigate();
-  const { isDark } = useTheme();
+  const { theme } = useTheme();
+  const isDark = theme === 'dark';
 
   // Валидация формы
   const validateForm = (): boolean => {
```

### src/pages/DeckEditorPage.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/pages/DeckEditorPage.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/pages/DeckEditorPage.tsx	2026-01-01 16:50:46
@@ -411,6 +411,36 @@
   };
 
   /**
+   * Редактирование изображения через миксин
+   */
+  const handleEditImage = async (wordId: number, mixin: string) => {
+    if (!deck) return;
+
+    try {
+      showInfo(t.words.editImage, {
+        description: `${t.words.editImageHint}: "${mixin}"`,
+      });
+
+      await deckService.editImage({
+        word_id: wordId,
+        mixin,
+      });
+
+      // Перезагружаем колоду с обновлёнными данными
+      await loadDeck();
+
+      showSuccess(t.decks.imageUpdated, {
+        description: t.decks.ready,
+      });
+    } catch (error) {
+      console.error(`Error editing image with mixin "${mixin}":`, error);
+      showError(t.decks.couldNotCreateImage, {
+        description: t.toast.tryAgain,
+      });
+    }
+  };
+
+  /**
    * Удаление изображения у слова
    */
   const handleDeleteImage = async (wordId: number) => {
@@ -798,6 +828,7 @@
           onDeleteWord={handleDeleteWord}
           onRegenerateImage={handleRegenerateImage}
           onRegenerateAudio={handleRegenerateAudio}
+          onEditImage={handleEditImage}
           onDeleteImage={handleDeleteImage}
           onDeleteAudio={handleDeleteAudio}
           onMoveCardToDeck={handleMoveCardToDeck}
```

### src/pages/MainPage.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/pages/MainPage.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/pages/MainPage.tsx	2026-01-02 18:33:07
@@ -1,4 +1,4 @@
-import { useState, useEffect } from 'react';
+import React, { useState, useEffect } from 'react';
 import { Card } from '../components/ui/card';
 import { Button } from '../components/ui/button';
 import { Label } from '../components/ui/label';
@@ -166,13 +166,14 @@
     }
     
     // Создаем или обновляем массив переводов
-    const updatedTranslations = processedWords.map((word) => {
-      // Ищем существующий перевод
-      const existing = translations.find((t) => t.word === word);
-      return existing || { word, translation: '' };
+    // ВАЖНО: Используем функциональную форму setTranslations для корректной работы с асинхронными операциями
+    setTranslations(prevTranslations => {
+      return processedWords.map((word) => {
+        // Ищем существующий перевод в предыдущем состоянии
+        const existing = prevTranslations.find((t) => t.word === word);
+        return existing || { word, translation: '' };
+      });
     });
-    
-    setTranslations(updatedTranslations);
   };
 
   /**
@@ -194,11 +195,17 @@
       return;
     }
 
+    // Логирование для отладки
+    console.log('🔍 [AutoTranslate] words:', words);
+    console.log('🔍 [AutoTranslate] translations:', translations);
+
     // Находим слова без перевода
     const wordsToTranslate = translations
       .filter((pair) => !pair.translation.trim())
       .map((pair) => pair.word);
 
+    console.log('🔍 [AutoTranslate] wordsToTranslate:', wordsToTranslate);
+
     if (wordsToTranslate.length === 0) {
       showInfo(t.toast.allTranslationsFilled);
       return;
@@ -213,6 +220,9 @@
     });
 
```

### src/pages/DecksPage.tsx
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/pages/DecksPage.tsx	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/pages/DecksPage.tsx	2026-01-02 17:28:45
@@ -289,9 +289,18 @@
   /**
    * Открыть модальное окно подтверждения инвертирования слов
    */
-  const openInvertWordsModal = (deck: Deck) => {
-    setSelectedDeckForInvert(deck);
-    setIsInvertWordsModalOpen(true);
+  const openInvertWordsModal = async (deck: Deck) => {
+    try {
+      // Загружаем полную информацию о колоде, чтобы получить слова с типами
+      const fullDeck = await deckService.getDeck(deck.id);
+      setSelectedDeckForInvert(fullDeck);
+      setIsInvertWordsModalOpen(true);
+    } catch (error) {
+      console.error('Error loading deck details:', error);
+      // Если не удалось загрузить, используем базовую информацию
+      setSelectedDeckForInvert(deck);
+      setIsInvertWordsModalOpen(true);
+    }
   };
 
   /**
```

### src/services/deck.service.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/services/deck.service.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/services/deck.service.ts	2026-01-01 16:46:05
@@ -435,6 +435,37 @@
   }
 
   /**
+   * Редактирование изображения через миксин
+   * Использует nano-banana-pro для image-to-image генерации
+   * @param data - Данные для редактирования
+   * @param signal - AbortSignal для отмены запроса
+   * @returns Promise с URL нового изображения
+   */
+  async editImage(
+    data: {
+      word_id: number;
+      mixin: string; // Что добавить/изменить на изображении (1-3 слова)
+    },
+    signal?: AbortSignal
+  ): Promise<{ image_url: string; mixin: string; word_id: number }> {
+    try {
+      // AI-редактирование изображений может занимать 60-120 секунд
+      const response = await api.post<{ image_url: string; mixin: string; word_id: number }>(
+        '/api/media/edit-image/',
+        data,
+        { 
+          timeout: 180000, // 3 минуты
+          signal, // Поддержка отмены запроса
+        }
+      );
+      return response.data;
+    } catch (error) {
+      console.error('Error editing image:', error);
+      throw error;
+    }
+  }
+
+  /**
    * Обновление медиа для слова в колоде
    * @param deckId - ID колоды
    * @param wordId - ID слова
```

### src/services/api.ts
```diff
--- /tmp/figma-diff-analysis/figma-repo/src/services/api.ts	2026-01-11 18:38:31
+++ /Users/andrei_prygunov/obsidian/deutsch/anki_cards/frontend/src/services/api.ts	2026-01-02 17:06:44
@@ -1,9 +1,13 @@
 import axios, { AxiosInstance, AxiosError } from 'axios';
 
 /**
- * Базовый URL для API через туннель (ngrok - постоянный домен)
+ * Базовый URL для API
+ * В продакшене: пустая строка (запросы на тот же домен)
+ * В разработке: localhost:8000 или ngrok URL из .env.development
  */
-const BASE_URL = 'https://get-anki.fan.ngrok.app';
+const BASE_URL = import.meta.env.VITE_API_BASE_URL?.startsWith('/') 
+  ? '' 
+  : (import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : ''));
 
 /**
  * Создание экземпляра Axios с настройками
```

---

## 📋 Файлы только в Figma (для справки)

Эти файлы есть в Figma репозитории, но отсутствуют в текущем.

**Действие:** Решить, нужно ли их добавить в текущий репозиторий или удалить из Figma.


*Файлов только в Figma не найдено*

---

## 📝 Инструкции по синхронизации

### Для новых файлов:
1. Откройте файл в текущем репозитории
2. Скопируйте его содержимое
3. Создайте файл с таким же путем в Figma
4. Вставьте содержимое

### Для измененных файлов:
1. Откройте файл в текущем репозитории
2. Сравните с версией в Figma (используйте детали изменений выше)
3. Обновите файл в Figma согласно изменениям

### Приоритет файлов:
1. **Высокий приоритет:** `src/` файлы (компоненты, страницы, сервисы)
2. **Средний приоритет:** Конфигурационные файлы (`package.json`, `vite.config.ts`)
3. **Низкий приоритет:** Документация, скрипты

---

## ⚠️ Важные замечания

- **НЕ удаляйте** файлы из Figma, которые есть только там (если не уверены)
- **НЕ перезаписывайте** файлы без проверки различий
- Сохраняйте резервные копии перед массовыми изменениями
- Проверяйте работу после синхронизации

---

**Сгенерировано автоматически скриптом:** `scripts/analyze_figma_diff.sh`

