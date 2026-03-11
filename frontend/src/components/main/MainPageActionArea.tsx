import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { GenerationProgress, GenerationStatus } from '../GenerationProgress';
import { GenerationSuccess } from '../GenerationSuccess';
import { TokenCostBadge } from '../TokenCostBadge';
import { InsufficientTokensModal } from '../InsufficientTokensModal';
import { Download, Loader2, Sparkles, ImageIcon, Volume2 } from 'lucide-react';

interface MainPageActionAreaProps {
  translations: { word: string; translation: string }[];
  generateImages: boolean;
  generateAudio: boolean;
  setGenerateImages: (val: boolean) => void;
  setGenerateAudio: (val: boolean) => void;
  isGenerating: boolean;
  generationStatus: GenerationStatus;
  generationProgress: { current: number; total: number; currentWord: string };
  hasMedia: boolean;
  deckName: string;
  setDeckName: (name: string) => void;
  savedDeckId: number | null;
  estimatedCost: number;
  balance: number;
  showInsufficientTokensModal: boolean;
  setShowInsufficientTokensModal: (val: boolean) => void;
  onGenerateMedia: () => Promise<void>;
  onCreateDeck: () => Promise<void>;
  onCancelGeneration: () => void;
  t: Record<string, any>;
}

export function MainPageActionArea({
  translations,
  generateImages,
  generateAudio,
  setGenerateImages,
  setGenerateAudio,
  isGenerating,
  generationStatus,
  generationProgress,
  hasMedia,
  deckName,
  setDeckName,
  savedDeckId,
  estimatedCost,
  balance,
  showInsufficientTokensModal,
  setShowInsufficientTokensModal,
  onGenerateMedia,
  onCreateDeck,
  onCancelGeneration,
  t,
}: MainPageActionAreaProps) {
  return (
    <>
      {/* Generation progress */}
      <GenerationProgress
        status={generationStatus}
        current={generationProgress.current}
        total={generationProgress.total}
        currentWord={generationProgress.currentWord}
        onCancel={onCancelGeneration}
      />

      {/* Success card */}
      {generationStatus === 'complete' && savedDeckId && (
        <GenerationSuccess
          deckName={deckName}
          deckId={savedDeckId}
          wordsCount={translations.length}
        />
      )}

      {/* Action area */}
      {translations.length > 0 && (
        <Card className="p-4">
          <div className="space-y-3">
            {/* Generate media button with token badge */}
            {!hasMedia && (
              <Button
                onClick={onGenerateMedia}
                disabled={
                  isGenerating ||
                  balance < estimatedCost ||
                  translations.length === 0
                }
                size="lg"
                className="h-12 w-full bg-gradient-to-r from-cyan-500 to-pink-500 hover:from-cyan-600 hover:to-pink-600"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    {t.generation.generatingMedia}
                  </>
                ) : balance < estimatedCost ? (
                  t.generation.insufficientTokens
                ) : (
                  <span className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    {t.generation.generateMedia}
                    <TokenCostBadge cost={estimatedCost} balance={balance} />
                  </span>
                )}
              </Button>
            )}

            {/* After media: deck name + create button */}
            {hasMedia && (
              <>
                <div className="flex items-center gap-2">
                  <Label htmlFor="deck-name" className="shrink-0 text-sm text-muted-foreground">
                    {t.decks.deckName}:
                  </Label>
                  <Input
                    id="deck-name"
                    value={deckName}
                    onChange={(e) => setDeckName(e.target.value)}
                    className="h-9"
                    disabled={isGenerating}
                  />
                </div>
                <Button
                  onClick={onCreateDeck}
                  disabled={isGenerating || !deckName.trim()}
                  size="lg"
                  className="h-12 w-full"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      {t.generation.creatingDeck}
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-5 w-5" />
                      {t.generation.createDeck}
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </Card>
      )}

      {/* Insufficient tokens modal */}
      <InsufficientTokensModal
        isOpen={showInsufficientTokensModal}
        onClose={() => setShowInsufficientTokensModal(false)}
        currentBalance={balance}
        requiredTokens={estimatedCost}
      />
    </>
  );
}
