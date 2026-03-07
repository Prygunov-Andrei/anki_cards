import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { EtymologyGenerator } from '../components/ai/EtymologyGenerator';
import { HintGenerator } from '../components/ai/HintGenerator';
import { SentenceGenerator } from '../components/ai/SentenceGenerator';
import { SynonymGenerator } from '../components/ai/SynonymGenerator';
import { WordCategoryManager } from '../components/words/WordCategoryManager';
import { LiteraryContextSection } from '../components/literary-context/LiteraryContextSection';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';
import { Word, WordSentence } from '../types';
import { deckService } from '../services/deck.service';
import { wordsService } from '../services/words.service';
import { toast } from 'sonner@2.0.3';

/**
 * Страница деталей слова с AI генерацией контента
 * Этап 7: AI Генерация контента
 */
const WordDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const t = useTranslation();
  const { user } = useAuthContext();
  const [word, setWord] = useState<Word | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Получаем deckId из state навигации
  const navState = (location.state || {}) as {
    deckId?: number;
    word?: string;
    translation?: string;
    fromTraining?: boolean;
    trainingState?: unknown;
  };
  const { deckId, word: wordFromState, translation: translationFromState } = navState;

  const handleBack = () => {
    if (navState.fromTraining && navState.trainingState) {
      navigate('/training/session', {
        state: navState.trainingState,
        replace: true,
      });
      return;
    }
    navigate(-1);
  };

  // Загрузка слова из API
  useEffect(() => {
    const loadWord = async () => {
      if (!id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        
        // Если есть deckId, загружаем колоду и находим слово
        if (deckId) {
          const deck = await deckService.getDeck(deckId);
          const foundWord = deck.words?.find(w => w.id === Number(id));
          
          if (foundWord) {
            console.log('📖 [WordDetailPage] Loaded word:', foundWord);
            console.log('  - id:', foundWord.id);
            console.log('  - original_word:', foundWord.original_word);
            console.log('  - etymology:', foundWord.etymology);
            console.log('  - etymology type:', typeof foundWord.etymology);
            console.log('  - etymology length:', foundWord.etymology?.length);
            console.log('  - hint_text:', foundWord.hint_text);
            console.log('  - sentences:', foundWord.sentences);
            console.log('  - All fields:', Object.keys(foundWord));
            setWord(foundWord);
          } else {
            console.error(`Word with id ${id} not found in deck ${deckId}`);
            toast.error(t.decks.wordNotFound || 'Слово не найдено');
          }
        } else {
          // Вход из каталога слов: загружаем по GET /api/words/{id}/
          try {
            const wordFromApi = await wordsService.getWord(Number(id));
            setWord(wordFromApi);
          } catch {
            if (wordFromState && translationFromState) {
              setWord({
                id: Number(id),
                original_word: wordFromState,
                translation: translationFromState,
                language: 'en',
                audio_file: null,
                image_file: null,
                etymology: '',
                sentences: [],
                notes: '',
                hint_text: '',
                hint_audio: null,
                part_of_speech: '',
                stickers: [],
                learning_status: 'new',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              });
            } else {
              toast.error(t.decks.wordNotFound || 'Слово не найдено');
            }
          }
        }
      } catch (error) {
        console.error('Error loading word:', error);
        toast.error(t.common.error || 'Ошибка загрузки');
      } finally {
        setIsLoading(false);
      }
    };

    loadWord();
  }, [id, deckId, wordFromState, translationFromState, t]);

  const handleEtymologyUpdate = async (etymology: string) => {
    if (!word) return;
    setWord({ ...word, etymology });
    try {
      if (deckId) {
        await deckService.updateWordAIContent(deckId, word.id, { etymology });
        const deck = await deckService.getDeck(deckId);
        const updatedWord = deck.words?.find(w => w.id === word.id);
        if (updatedWord) setWord(updatedWord);
      } else {
        await wordsService.updateWord(word.id, { etymology });
        const updated = await wordsService.getWord(word.id);
        setWord(updated);
      }
    } catch (error) {
      console.error('Failed to save etymology:', error);
      toast.error(t.common.error || 'Ошибка сохранения');
    }
  };

  const handleHintUpdate = async (hintText: string, hintAudio: string | null) => {
    if (!word) return;
    setWord({ ...word, hint_text: hintText, hint_audio: hintAudio });
    try {
      if (deckId) {
        await deckService.updateWordAIContent(deckId, word.id, {
          hint_text: hintText,
          hint_audio: hintAudio,
        });
        const deck = await deckService.getDeck(deckId);
        const updatedWord = deck.words?.find(w => w.id === word.id);
        if (updatedWord) setWord(updatedWord);
      } else {
        await wordsService.updateWord(word.id, { hint_text: hintText });
        const updated = await wordsService.getWord(word.id);
        setWord(updated);
      }
    } catch (error) {
      console.error('Failed to save hint:', error);
      toast.error(t.common.error || 'Ошибка сохранения');
    }
  };

  const handleSentencesUpdate = async (sentences: WordSentence[]) => {
    if (!word) return;
    setWord({ ...word, sentences });
    try {
      if (deckId) {
        await deckService.updateWordAIContent(deckId, word.id, { sentences });
        const deck = await deckService.getDeck(deckId);
        const updatedWord = deck.words?.find(w => w.id === word.id);
        if (updatedWord) setWord(updatedWord);
      } else {
        await wordsService.updateWord(word.id, { sentences });
        const updated = await wordsService.getWord(word.id);
        setWord(updated);
      }
    } catch (error) {
      console.error('Failed to save sentences:', error);
      toast.error(t.common.error || 'Ошибка сохранения');
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!word) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-lg text-gray-600">{t.decks.wordNotFound}</p>
            <Button onClick={() => navigate(deckId ? '/decks' : '/words')} className="mt-4">
              {t.decks.backToDecks}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-6 pb-20">
      {/* Заголовок */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={handleBack}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t.common.back}
        </Button>
        
        <div className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 p-4 sm:p-6 text-white shadow-lg">
          <h1 className="mb-2 text-2xl sm:text-3xl font-bold">{word.original_word}</h1>
          <p className="text-xl opacity-90">{word.translation}</p>
          {word.part_of_speech && (
            <p className="mt-2 text-sm opacity-75">
              {word.part_of_speech.toUpperCase()}
            </p>
          )}
        </div>
      </div>

      {/* Табы */}
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-3 sm:grid-cols-5">
          <TabsTrigger value="basic">Основное</TabsTrigger>
          <TabsTrigger value="etymology">Этимология</TabsTrigger>
          <TabsTrigger value="sentences">Примеры</TabsTrigger>
          <TabsTrigger value="hints">Подсказки</TabsTrigger>
          <TabsTrigger value="synonyms">Связи</TabsTrigger>
        </TabsList>

        {/* Таб: Основное */}
        <TabsContent value="basic" className="mt-6 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Основная информация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Слово</label>
                <p className="mt-1 text-lg font-semibold">{word.original_word}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Перевод</label>
                <p className="mt-1 text-lg">{word.translation}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Часть речи</label>
                <p className="mt-1 text-lg">{word.part_of_speech || 'Не указано'}</p>
              </div>
              {word.notes && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Заметки</label>
                  <p className="mt-1 text-gray-600">{word.notes}</p>
                </div>
              )}

              {/* Категории */}
              <WordCategoryManager
                wordId={word.id}
                currentCategories={word.categories || []}
                onCategoriesChange={(categories) => setWord({ ...word, categories })}
              />
            </CardContent>
          </Card>

          {/* Literary Context */}
          <LiteraryContextSection
            wordId={word.id}
            activeSource={user?.active_literary_source ?? null}
            literaryContext={word.literary_context}
          />
        </TabsContent>

        {/* Таб: Этимология */}
        <TabsContent value="etymology" className="mt-6">
          <EtymologyGenerator
            wordId={word.id}
            etymology={word.etymology}
            onEtymologyUpdate={handleEtymologyUpdate}
            deckId={deckId}
          />
        </TabsContent>

        {/* Таб: Примеры предложений */}
        <TabsContent value="sentences" className="mt-6">
          <SentenceGenerator
            wordId={word.id}
            sentences={word.sentences}
            onSentencesUpdate={handleSentencesUpdate}
            deckId={deckId}
          />
        </TabsContent>

        {/* Таб: Подсказки */}
        <TabsContent value="hints" className="mt-6">
          <HintGenerator
            wordId={word.id}
            hintText={word.hint_text}
            hintAudio={word.hint_audio}
            onHintUpdate={handleHintUpdate}
            deckId={deckId}
          />
        </TabsContent>

        {/* Таб: Синонимы и связи */}
        <TabsContent value="synonyms" className="mt-6 space-y-6">
          <SynonymGenerator
            wordId={word.id}
            onSynonymCreated={(synonym) => {
              console.log('Synonym created:', synonym);
            }}
          />
          
          {/* Информация */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="py-4">
              <p className="text-sm text-blue-800">
                💡 <strong>Совет:</strong> Синонимы помогают расширить словарный запас и
                связать похожие слова между собой. При создании синонима автоматически
                создается связь между словами.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WordDetailPage;