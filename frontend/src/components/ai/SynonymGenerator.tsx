import React, { useState } from 'react';
import { Sparkles, Loader2, ArrowRight } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { aiGenerationService } from '../../services/ai-generation.service';
import { useTokenContext } from '../../contexts/TokenContext';
import { toast } from 'sonner@2.0.3';
import { useTranslation } from '../../contexts/LanguageContext';
import { Word } from '../../types';
import axios from 'axios';

interface SynonymGeneratorProps {
  wordId: number;
  onSynonymCreated?: (synonym: Word) => void;
}

/**
 * Компонент для генерации синонимов
 * Этап 7: AI Генерация контента
 */
export const SynonymGenerator: React.FC<SynonymGeneratorProps> = ({
  wordId,
  onSynonymCreated,
}) => {
  const t = useTranslation();
  const { refreshBalance } = useTokenContext();
  const [isLoading, setIsLoading] = useState(false);
  const [createCard, setCreateCard] = useState(true);
  const [lastGeneratedSynonym, setLastGeneratedSynonym] = useState<Word | null>(null);

  const handleGenerate = async () => {
    try {
      setIsLoading(true);
      
      const response = await aiGenerationService.generateSynonym({
        word_id: wordId,
        create_card: createCard,
      });

      setLastGeneratedSynonym(response.synonym_word);
      await refreshBalance();
      
      if (onSynonymCreated) {
        onSynonymCreated(response.synonym_word);
      }
      
      toast.success(t.ai.synonymGenerated, {
        description: `${response.synonym_word.original_word} • ${t.tokens.spent}: ${response.tokens_spent}`,
      });
    } catch (error: unknown) {
      console.error('Synonym generation error:', error);
      
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

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-2xl">🔗</span>
          {t.ai.synonyms}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Последний сгенерированный синоним */}
        {lastGeneratedSynonym && (
          <div className="rounded-lg bg-gradient-to-r from-purple-100 to-pink-100 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="bg-white">
                {t.ai.new}
              </Badge>
              <div className="flex flex-1 items-center gap-2">
                <span className="font-medium text-gray-900">
                  {lastGeneratedSynonym.original_word}
                </span>
                <ArrowRight className="h-4 w-4 text-gray-400" />
                <span className="text-gray-600">
                  {lastGeneratedSynonym.translation}
                </span>
              </div>
            </div>
          </div>
        )}

        {!lastGeneratedSynonym && (
          <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            {t.ai.noSynonyms}
          </div>
        )}

        {/* Опция создания карточки */}
        <div className="flex items-center space-x-2 rounded-lg bg-white p-3 shadow-sm">
          <Checkbox
            id="create-card"
            checked={createCard}
            onCheckedChange={(checked) => setCreateCard(checked === true)}
            disabled={isLoading}
          />
          <Label
            htmlFor="create-card"
            className="cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {t.ai.createCard}
          </Label>
        </div>

        {/* Кнопка генерации */}
        <Button
          onClick={handleGenerate}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t.ai.generating}
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              {t.ai.generateSynonym}
            </>
          )}
        </Button>

        {/* Информация */}
        <div className="rounded-lg bg-blue-50 p-3 text-xs text-blue-700">
          <p className="font-medium">{t.ai.synonymInfo}</p>
          <p className="mt-1 text-blue-600">{t.ai.synonymDescription}</p>
        </div>
      </CardContent>
    </Card>
  );
};