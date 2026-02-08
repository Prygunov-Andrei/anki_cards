import React, { useState } from 'react';
import { Sparkles, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { aiGenerationService } from '../../services/ai-generation.service';
import { deckService } from '../../services/deck.service';
import { useTokenContext } from '../../contexts/TokenContext';
import { toast } from 'sonner@2.0.3';
import { useTranslation } from '../../contexts/LanguageContext';
import axios from 'axios';

interface EtymologyGeneratorProps {
  wordId: number;
  etymology: string;
  onEtymologyUpdate: (etymology: string) => void;
  deckId?: number; // Добавляем deckId для перезагрузки
}

/**
 * Компонент для генерации и отображения этимологии слова
 * Этап 7: AI Генерация контента
 */
export const EtymologyGenerator: React.FC<EtymologyGeneratorProps> = ({
  wordId,
  etymology,
  onEtymologyUpdate,
  deckId,
}) => {
  const t = useTranslation();
  const { refreshBalance } = useTokenContext();
  const [isLoading, setIsLoading] = useState(false);

  // Защита от undefined/null значений
  const safeEtymology = etymology || '';

  const handleGenerate = async (forceRegenerate: boolean = false) => {
    try {
      setIsLoading(true);
      
      const response = await aiGenerationService.generateEtymology({
        word_id: wordId,
        force_regenerate: forceRegenerate,
      });

      onEtymologyUpdate(response.etymology);
      await refreshBalance();
      
      toast.success(t.ai.etymologyGenerated, {
        description: `${t.tokens.spent}: ${response.tokens_spent}`,
      });
    } catch (error: unknown) {
      console.error('Etymology generation error:', error);
      if (axios.isAxiosError(error)) {
        console.log('🔍 [Error Debug] Full error object:', JSON.stringify(error.response?.data, null, 2));
      }
      
      const errorMessage = axios.isAxiosError(error)
        ? (error.response?.data?.detail || error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : undefined);
      console.log('🔍 [Error Debug] Error message:', errorMessage);
      
      // Если этимология уже существует, пытаемся загрузить её с бекенда
      if (errorMessage?.includes('already exists') || errorMessage?.includes('уже существует')) {
        console.log('⚠️ Etymology already exists, trying to load from backend...');
        console.log('🔍 [Debug] deckId:', deckId);
        console.log('🔍 [Debug] wordId:', wordId);
        
        // Пытаемся перезагрузить слово, если есть deckId
        if (deckId) {
          try {
            console.log('🔄 Loading deck...');
            const deck = await deckService.getDeck(deckId);
            console.log('✅ Deck loaded, words count:', deck.words?.length);
            
            const updatedWord = deck.words?.find(w => w.id === wordId);
            
            console.log('🔍 [Debug] Found word:', updatedWord);
            console.log('🔍 [Debug] Etymology value:', updatedWord?.etymology);
            console.log('🔍 [Debug] Etymology type:', typeof updatedWord?.etymology);
            console.log('🔍 [Debug] Etymology length:', updatedWord?.etymology?.length);
            console.log('🔍 [Debug] All word fields:', Object.keys(updatedWord || {}));
            
            if (updatedWord) {
              if (updatedWord.etymology && updatedWord.etymology.trim().length > 0) {
                console.log('✅ Found existing etymology:', updatedWord.etymology);
                onEtymologyUpdate(updatedWord.etymology);
                toast.success('Этимология загружена с бекенда', {
                  description: 'Используйте кнопку "Перегенерировать" для создания новой версии',
                });
                return; // ВАЖНО: выходим, чтобы не показывать ошибку ниже
              } else {
                console.log('⚠️ Etymology exists on backend but is empty string');
                console.log('🔍 [Debug] Checking if etymology is in response...');
                // Не показываем toast.warning, только логируем
              }
            } else {
              console.log('❌ Word not found in deck');
            }
          } catch (loadError) {
            console.error('❌ Failed to load existing etymology:', loadError);
          }
        } else {
          console.log('⚠️ No deckId provided, cannot reload from backend');
        }
        
        // Показываем сообщение только один раз
        toast.info('Этимология уже существует на бекенде', {
          description: 'Нажмите кнопку "Перегенерировать" (🔄) ниже для создания новой версии',
        });
        return; // ВАЖНО: выходим, чтобы не обрабатывать другие ошибки
      } 
      
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

  const hasEtymology = safeEtymology && safeEtymology.trim().length > 0;

  return (
    <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-2xl">📖</span>
          {t.ai.etymology}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {hasEtymology ? (
          <div className="rounded-lg bg-white p-4 text-sm leading-relaxed text-gray-700 shadow-sm">
            {safeEtymology}
          </div>
        ) : (
          <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            {t.ai.noEtymology}
          </div>
        )}

        <div className="flex gap-2">
          {hasEtymology ? (
            <Button
              onClick={() => handleGenerate(true)}
              disabled={isLoading}
              variant="outline"
              className="flex-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.ai.generating}
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  {t.ai.regenerate}
                </>
              )}
            </Button>
          ) : (
            <>
              <Button
                onClick={() => handleGenerate(false)}
                disabled={isLoading}
                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t.ai.generating}
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    {t.ai.generateEtymology}
                  </>
                )}
              </Button>
              <Button
                onClick={() => handleGenerate(true)}
                disabled={isLoading}
                variant="outline"
                className="shrink-0"
                title="Перегенерировать (force_regenerate=true)"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};