import React, { useState } from 'react';
import { Sparkles, Loader2, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { aiGenerationService } from '../../services/ai-generation.service';
import { useTokenContext } from '../../contexts/TokenContext';
import { toast } from 'sonner@2.0.3';
import { useTranslation } from '../../contexts/LanguageContext';
import { WordSentence } from '../../types';
import axios from 'axios';
import { logger } from '../../utils/logger';

interface SentenceGeneratorProps {
  wordId: number;
  sentences: WordSentence[];
  onSentencesUpdate: (sentences: WordSentence[]) => void;
  deckId?: number; // Добавляем deckId для перезагрузки
}

/**
 * Компонент для генерации и управления предложениями
 * Этап 7: AI Генерация контента
 */
export const SentenceGenerator: React.FC<SentenceGeneratorProps> = ({
  wordId,
  sentences,
  onSentencesUpdate,
  deckId,
}) => {
  const t = useTranslation();
  const { refreshBalance } = useTokenContext();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCount, setSelectedCount] = useState(3);
  const [context, setContext] = useState('');

  // Защита от undefined/null значений
  const safeSentences = sentences || [];

  const handleGenerate = async () => {
    try {
      setIsLoading(true);
      
      const response = await aiGenerationService.generateSentences({
        word_id: wordId,
        count: selectedCount,
        context: context.trim() || undefined,
      });

      // Добавляем новые предложения к существующим
      // Backend возвращает массив строк, преобразуем в WordSentence
      const newSentences: WordSentence[] = response.sentences.map(text => ({
        sentence: text,
        source: 'ai' as const,
      }));
      
      onSentencesUpdate([...safeSentences, ...newSentences]);
      await refreshBalance();
      
      toast.success(t.ai.sentencesGenerated, {
        description: `${t.tokens.spent}: ${response.tokens_spent}`,
      });
      
      // Очищаем контекст после успешной генерации
      setContext('');
    } catch (error: unknown) {
      logger.error('Sentences generation error:', error);
      
      const errorMessage = axios.isAxiosError(error)
        ? (error.response?.data?.detail || error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : undefined);
      
      if (errorMessage?.includes('Недостаточно токенов') || errorMessage?.includes('Insufficient tokens')) {
        toast.error(t.errors.insufficientTokens, {
          description: t.errors.pleaseTopUp,
        });
      } else {
        toast.error(t.errors.generationFailed, {
          description: errorMessage,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveSentence = (index: number) => {
    const updatedSentences = safeSentences.filter((_, i) => i !== index);
    onSentencesUpdate(updatedSentences);
    toast.success(t.ai.sentenceRemoved);
  };

  const counts = [1, 2, 3, 4, 5];

  return (
    <Card className="border-green-200 bg-gradient-to-br from-green-50 to-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-2xl">📝</span>
          {t.ai.sentences}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Список существующих предложений */}
        {safeSentences.length > 0 && (
          <div className="space-y-2">
            {safeSentences.map((sentence, index) => (
              <div
                key={index}
                className="group relative rounded-lg bg-white p-3 pr-10 text-sm leading-relaxed text-gray-700 shadow-sm transition-all hover:shadow-md"
              >
                <div className="flex items-start gap-2">
                  <Badge variant={sentence.source === 'ai' ? 'default' : 'secondary'} className="mt-0.5 shrink-0">
                    {sentence.source === 'ai' ? '🤖 AI' : '👤 User'}
                  </Badge>
                  <span className="flex-1">{sentence.sentence}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveSentence(index)}
                  className="absolute right-1 top-1 h-7 w-7 p-0 opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <X className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {safeSentences.length === 0 && (
          <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            {t.ai.noSentences}
          </div>
        )}

        {/* Выбор количества */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            {t.ai.sentenceCount}
          </label>
          <div className="flex gap-2">
            {counts.map((count) => (
              <Button
                key={count}
                variant={selectedCount === count ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCount(count)}
                disabled={isLoading}
                className="flex-1"
              >
                {count}
              </Button>
            ))}
          </div>
        </div>

        {/* Контекст (опционально) */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            {t.ai.context} <span className="text-gray-400">({t.ai.optional})</span>
          </label>
          <Textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder={t.ai.contextPlaceholder}
            disabled={isLoading}
            rows={3}
            className="resize-none"
          />
        </div>

        {/* Кнопка генерации */}
        <Button
          onClick={handleGenerate}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t.ai.generating}
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              {t.ai.generateSentences}
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};