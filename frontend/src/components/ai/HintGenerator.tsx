import React, { useState } from 'react';
import { Sparkles, RefreshCw, Loader2, Volume2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { AudioPlayer } from '../AudioPlayer';
import { aiGenerationService } from '../../services/ai-generation.service';
import { useTokenContext } from '../../contexts/TokenContext';
import { toast } from 'sonner@2.0.3';
import { useTranslation } from '../../contexts/LanguageContext';
import axios from 'axios';

interface HintGeneratorProps {
  wordId: number;
  hintText: string;
  hintAudio: string | null;
  onHintUpdate: (hintText: string, hintAudio: string | null) => void;
  deckId?: number; // Добавляем deckId для перезагрузки
}

/**
 * Компонент для генерации и отображения подсказок (текст + аудио)
 * Этап 7: AI Генерация контента
 */
export const HintGenerator: React.FC<HintGeneratorProps> = ({
  wordId,
  hintText,
  hintAudio,
  onHintUpdate,
  deckId,
}) => {
  const t = useTranslation();
  const { refreshBalance } = useTokenContext();
  const [isLoading, setIsLoading] = useState(false);
  const [generateAudio, setGenerateAudio] = useState(true);

  // Защита от undefined/null значений
  const safeHintText = hintText || '';
  const safeHintAudio = hintAudio || null;

  const handleGenerate = async (forceRegenerate: boolean = false) => {
    try {
      setIsLoading(true);
      
      const response = await aiGenerationService.generateHint({
        word_id: wordId,
        force_regenerate: forceRegenerate,
        generate_audio: generateAudio,
      });

      onHintUpdate(response.hint_text, response.hint_audio_url || null);
      await refreshBalance();
      
      toast.success(t.ai.hintGenerated, {
        description: `${t.tokens.spent}: ${response.tokens_spent}`,
      });
    } catch (error: unknown) {
      console.error('Hint generation error:', error);
      
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

  const hasHint = safeHintText && safeHintText.trim().length > 0;

  return (
    <Card className="border-yellow-200 bg-gradient-to-br from-yellow-50 to-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-2xl"></span>
          {t.ai.hint}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {hasHint ? (
          <div className="space-y-3">
            <div className="rounded-lg bg-white p-4 text-sm leading-relaxed text-gray-700 shadow-sm">
              {safeHintText}
            </div>
            
            {safeHintAudio && (
              <div className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 p-3">
                <Volume2 className="h-5 w-5 text-purple-500" />
                <AudioPlayer 
                  audioSrc={safeHintAudio}
                  className="flex-1"
                />
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
            {t.ai.noHint}
          </div>
        )}

        <div className="flex items-center space-x-2 rounded-lg bg-white p-3 shadow-sm">
          <Checkbox
            id="generate-audio"
            checked={generateAudio}
            onCheckedChange={(checked) => setGenerateAudio(checked === true)}
            disabled={isLoading}
          />
          <Label
            htmlFor="generate-audio"
            className="cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {t.ai.generateAudio}
          </Label>
        </div>

        <div className="flex gap-2">
          {hasHint ? (
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
            <Button
              onClick={() => handleGenerate(false)}
              disabled={isLoading}
              className="flex-1 bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.ai.generating}
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  {t.ai.generateHint}
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};