# Инструкция: Правильная генерация .apkg файлов

## ⚠️ КРИТИЧЕСКИ ВАЖНО

**Проблема:** Фронтенд генерирует .apkg файлы размером 50-60 KB вместо ожидаемых 8-9 MB. Это означает, что **медиафайлы (изображения и аудио) НЕ добавляются в .apkg**.

**Причина:** Медиафайлы должны быть **уже сохранены в базе данных** в словах колоды перед генерацией .apkg. Бэкенд автоматически извлекает медиафайлы из слов колоды, но если медиафайлы не были сгенерированы или не сохранены в словах, они не попадут в .apkg.

---

## 📋 Правильный процесс генерации .apkg

### Вариант 1: Генерация .apkg из существующей колоды

**Используйте этот вариант, когда:**
- Колода уже создана и сохранена в "Мои колоды"
- Слова в колоде уже имеют сгенерированные изображения и аудио

#### Шаги:

1. **Убедитесь, что в колоде есть медиафайлы:**
   ```typescript
   // Получаем колоду с деталями
   const deck = await api.get(`/cards/decks/${deckId}/`);
   
   // Проверяем, что у слов есть медиафайлы
   const wordsWithMedia = deck.data.words.filter(
     word => word.image_file && word.audio_file
   );
   
   if (wordsWithMedia.length === 0) {
     alert('⚠️ В колоде нет медиафайлов! Сначала сгенерируйте изображения и аудио для слов.');
     return;
   }
   ```

2. **Генерируйте .apkg файл:**
   ```typescript
   // POST /api/cards/decks/{deck_id}/generate/
   const response = await api.post(`/cards/decks/${deckId}/generate/`);
   
   // Ответ:
   // {
   //   file_id: "uuid-string",
   //   download_url: "/api/cards/download/{file_id}/",
   //   deck_name: "Название колоды",
   //   cards_count: 76
   // }
   ```

3. **Скачивайте файл:**
   ```typescript
   const fileId = response.data.file_id;
   
   // GET /api/cards/download/{file_id}/
   const blob = await api.get(`/cards/download/${fileId}/`, {
     responseType: 'blob'
   });
   
   // Создаем ссылку для скачивания
   const url = window.URL.createObjectURL(blob);
   const a = document.createElement('a');
   a.href = url;
   a.download = `${response.data.deck_name}.apkg`;
   document.body.appendChild(a);
   a.click();
   window.URL.revokeObjectURL(url);
   document.body.removeChild(a);
   ```

#### ✅ Проверка успешности:

- **Размер файла должен быть:** 8-9 MB для колоды с 38 словами (76 медиафайлов)
- **Если размер 50-60 KB:** медиафайлы не добавлены — проверьте, что слова имеют `image_file` и `audio_file`

---

### Вариант 2: Быстрая генерация (без сохранения в колоду)

**Используйте этот вариант для быстрой генерации из списка слов.**

#### Шаги:

1. **Генерируйте медиафайлы для каждого слова:**
   ```typescript
   const words = ['Haus', 'Auto', 'Buch'];
   const mediaFiles = {
     images: {},
     audio: {}
   };
   
   for (const word of words) {
     // Генерируем изображение
     const imageResponse = await api.post('/media/generate-image/', {
       word: word,
       translation: translations[word],
       language: 'de',
       image_style: 'balanced'
     });
     mediaFiles.images[word] = imageResponse.data.image_url;
     
     // Генерируем аудио
     const audioResponse = await api.post('/media/generate-audio/', {
       word: word,
       language: 'de'
     });
     mediaFiles.audio[word] = audioResponse.data.audio_url;
   }
   ```

2. **Генерируйте .apkg с медиафайлами:**
   ```typescript
   // POST /api/cards/generate/
   const response = await api.post('/cards/generate/', {
     words: words.join(','),
     language: 'de',
     translations: translations,
     deck_name: 'Новая колода',
     image_files: mediaFiles.images,  // ⚠️ ОБЯЗАТЕЛЬНО!
     audio_files: mediaFiles.audio,   // ⚠️ ОБЯЗАТЕЛЬНО!
     save_to_decks: false
   });
   ```

3. **Скачивайте файл:**
   ```typescript
   const fileId = response.data.file_id;
   const blob = await api.get(`/cards/download/${fileId}/`, {
     responseType: 'blob'
   });
   // ... (код скачивания как выше)
   ```

#### ⚠️ КРИТИЧЕСКИ ВАЖНО:

- **Обязательно передавайте `image_files` и `audio_files`** в запросе `POST /api/cards/generate/`
- Эти параметры должны быть словарями: `{ 'слово': 'URL_к_файлу' }`
- URL должны быть полными (например, `https://get-anki.fan.ngrok.app/media/images/...`)

---

## 🔍 Диагностика проблем

### Проблема: Размер .apkg файла 50-60 KB

**Возможные причины:**

1. **Медиафайлы не были сгенерированы:**
   ```typescript
   // Проверьте, что слова имеют медиафайлы
   const deck = await api.get(`/cards/decks/${deckId}/`);
   console.log('Слова с медиа:', deck.data.words.filter(w => w.image_file && w.audio_file));
   ```

2. **Медиафайлы не переданы в запросе:**
   ```typescript
   // При быстрой генерации проверьте, что передаете:
   console.log('image_files:', image_files);  // Должен быть объект
   console.log('audio_files:', audio_files);  // Должен быть объект
   ```

3. **URL медиафайлов неправильные:**
   ```typescript
   // URL должны быть полными и доступными
   // ✅ Правильно: 'https://get-anki.fan.ngrok.app/media/images/xxx.jpg'
   // ❌ Неправильно: '/media/images/xxx.jpg'
   // ❌ Неправильно: 'images/xxx.jpg'
   ```

### Проверка в консоли браузера:

```typescript
// После генерации .apkg проверьте размер файла
const blob = await api.get(`/cards/download/${fileId}/`, {
  responseType: 'blob'
});

console.log('Размер .apkg файла:', blob.size, 'байт');
console.log('Размер в KB:', blob.size / 1024);
console.log('Размер в MB:', blob.size / 1024 / 1024);

// Для колоды с 38 словами (76 медиафайлов) должно быть ~8-9 MB
if (blob.size < 100000) {  // Меньше 100 KB
  console.error('⚠️ ПРОБЛЕМА: Медиафайлы не добавлены!');
}
```

---

## 📝 Пример полного кода

### Генерация .apkg из существующей колоды:

```typescript
async function generateApkgFromDeck(deckId: number) {
  try {
    // 1. Проверяем колоду
    const deckResponse = await api.get(`/cards/decks/${deckId}/`);
    const deck = deckResponse.data;
    
    if (deck.words.length === 0) {
      throw new Error('Колода пуста');
    }
    
    const wordsWithMedia = deck.words.filter(
      w => w.image_file && w.audio_file
    );
    
    if (wordsWithMedia.length === 0) {
      throw new Error('В колоде нет медиафайлов. Сначала сгенерируйте изображения и аудио.');
    }
    
    console.log(`✅ Найдено ${wordsWithMedia.length} слов с медиафайлами`);
    
    // 2. Генерируем .apkg
    const generateResponse = await api.post(`/cards/decks/${deckId}/generate/`);
    const fileId = generateResponse.data.file_id;
    
    console.log('✅ .apkg файл создан:', fileId);
    
    // 3. Скачиваем файл
    const blob = await api.get(`/cards/download/${fileId}/`, {
      responseType: 'blob'
    });
    
    // Проверяем размер
    const sizeMB = blob.size / 1024 / 1024;
    console.log(`📦 Размер файла: ${sizeMB.toFixed(2)} MB`);
    
    if (sizeMB < 1) {
      console.warn('⚠️ ВНИМАНИЕ: Размер файла слишком мал! Медиафайлы могут отсутствовать.');
    }
    
    // Скачиваем
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${deck.name}.apkg`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return { success: true, fileId, sizeMB };
  } catch (error) {
    console.error('Ошибка генерации .apkg:', error);
    throw error;
  }
}
```

### Быстрая генерация .apkg:

```typescript
async function quickGenerateApkg(
  words: string[],
  translations: Record<string, string>,
  language: string = 'de'
) {
  try {
    const imageFiles: Record<string, string> = {};
    const audioFiles: Record<string, string> = {};
    
    // 1. Генерируем медиафайлы для каждого слова
    console.log('🎨 Генерация медиафайлов...');
    
    for (const word of words) {
      // Изображение
      const imageRes = await api.post('/media/generate-image/', {
        word: word,
        translation: translations[word],
        language: language,
        image_style: 'balanced'
      });
      imageFiles[word] = imageRes.data.image_url;
      
      // Аудио
      const audioRes = await api.post('/media/generate-audio/', {
        word: word,
        language: language
      });
      audioFiles[word] = audioRes.data.audio_url;
      
      console.log(`✅ ${word}: изображение и аудио готовы`);
    }
    
    // 2. Генерируем .apkg
    console.log('📦 Генерация .apkg файла...');
    
    const generateResponse = await api.post('/cards/generate/', {
      words: words.join(','),
      language: language,
      translations: translations,
      deck_name: 'Быстрая генерация',
      image_files: imageFiles,  // ⚠️ ОБЯЗАТЕЛЬНО!
      audio_files: audioFiles,   // ⚠️ ОБЯЗАТЕЛЬНО!
      save_to_decks: false
    });
    
    const fileId = generateResponse.data.file_id;
    
    // 3. Скачиваем файл
    const blob = await api.get(`/cards/download/${fileId}/`, {
      responseType: 'blob'
    });
    
    const sizeMB = blob.size / 1024 / 1024;
    console.log(`📦 Размер файла: ${sizeMB.toFixed(2)} MB`);
    
    if (sizeMB < 1) {
      console.warn('⚠️ ВНИМАНИЕ: Размер файла слишком мал!');
    }
    
    // Скачиваем
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Быстрая_генерация.apkg`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return { success: true, fileId, sizeMB };
  } catch (error) {
    console.error('Ошибка быстрой генерации .apkg:', error);
    throw error;
  }
}
```

---

## ✅ Чек-лист перед генерацией .apkg

- [ ] Колода содержит слова (проверено через `GET /api/cards/decks/{id}/`)
- [ ] Слова имеют медиафайлы (`image_file` и `audio_file` не null)
- [ ] При быстрой генерации переданы `image_files` и `audio_files` в запросе
- [ ] URL медиафайлов полные и доступные
- [ ] После генерации проверен размер файла (должен быть > 1 MB для колоды с медиа)
- [ ] Файл успешно скачивается и открывается в Anki

---

## 📞 Если проблема сохраняется

1. **Проверьте логи бэкенда:**
   - Должны быть сообщения `✅ Добавлен аудиофайл` и `✅ Добавлен файл изображения`
   - Если есть `❌ Файл не найден` — медиафайлы не сохранены в БД

2. **Проверьте ответ API:**
   ```typescript
   const response = await api.post(`/cards/decks/${deckId}/generate/`);
   console.log('Ответ API:', response.data);
   // Должен содержать: file_id, download_url, deck_name, cards_count
   ```

3. **Проверьте размер скачанного файла:**
   ```typescript
   const blob = await api.get(`/cards/download/${fileId}/`, {
     responseType: 'blob'
   });
   console.log('Размер файла:', blob.size);
   // Для 38 слов должно быть ~8-9 MB
   ```

---

**Последнее обновление:** 7 декабря 2025

