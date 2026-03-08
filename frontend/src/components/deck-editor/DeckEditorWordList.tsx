import React from 'react';
import { Deck, Word } from '../../types';
import { WordsTable } from '../WordsTable';
import { Button } from '../ui/button';
import { Download, Loader2 } from 'lucide-react';
import { getLanguageName } from '../../utils/language-helpers';
import { useTranslation } from '../../contexts/LanguageContext';

interface DeckEditorWordListProps {
  deck: Deck;
  allDecks: Deck[];
  isGenerating: boolean;
  onDeleteWord: (wordId: number) => Promise<void>;
  onRegenerateImage: (wordId: number, word: string, translation: string) => Promise<void>;
  onRegenerateAudio: (wordId: number, word: string) => Promise<void>;
  onEditImage: (wordId: number, mixin: string) => Promise<void>;
  onDeleteImage: (wordId: number) => Promise<void>;
  onDeleteAudio: (wordId: number) => Promise<void>;
  onMoveCardToDeck: (wordId: number, toDeckId: number, toDeckName: string) => Promise<void>;
  onInvertWord: (wordId: number) => Promise<void>;
  onCreateEmptyCard: (wordId: number) => Promise<void>;
  onWordUpdate: (wordId: number, data: { original_word?: string; translation?: string }) => Promise<void>;
  onGenerateApkg: () => Promise<void>;
}

export const DeckEditorWordList: React.FC<DeckEditorWordListProps> = ({
  deck,
  allDecks,
  isGenerating,
  onDeleteWord,
  onRegenerateImage,
  onRegenerateAudio,
  onEditImage,
  onDeleteImage,
  onDeleteAudio,
  onMoveCardToDeck,
  onInvertWord,
  onCreateEmptyCard,
  onWordUpdate,
  onGenerateApkg,
}) => {
  const t = useTranslation();

  return (
    <>
      {/* Таблица слов */}
      <div className="mb-6">
        <WordsTable
          words={deck.words}
          deckId={deck.id}
          onDeleteWord={onDeleteWord}
          onRegenerateImage={onRegenerateImage}
          onRegenerateAudio={onRegenerateAudio}
          onEditImage={onEditImage}
          onDeleteImage={onDeleteImage}
          onDeleteAudio={onDeleteAudio}
          onMoveCardToDeck={onMoveCardToDeck}
          onInvertWord={onInvertWord}
          onCreateEmptyCard={onCreateEmptyCard}
          onWordUpdate={onWordUpdate}
          allDecks={allDecks.filter(d => d.id !== deck.id)}
          targetLang={getLanguageName(deck.target_lang)}
          sourceLang={getLanguageName(deck.source_lang)}
        />
      </div>

      {/* Кнопка экспорта .apkg (внизу, после списка слов) */}
      {deck.words && deck.words.length > 0 && (
        <div className="flex justify-center">
          <Button
            onClick={onGenerateApkg}
            disabled={isGenerating}
            variant="default"
            size="lg"
            className="w-full sm:w-auto"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {t.decks.generating}
              </>
            ) : (
              <>
                <Download className="mr-2 h-5 w-5" />
                {t.decks.generateApkg}
              </>
            )}
          </Button>
        </div>
      )}
    </>
  );
};
