import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Deck } from '../../types';
import { EditableText } from '../EditableText';
import { Button } from '../ui/button';
import { ArrowLeft, GraduationCap } from 'lucide-react';
import { useTranslation } from '../../contexts/LanguageContext';

interface DeckEditorHeaderProps {
  deck: Deck;
  onSaveTitle: (newTitle: string) => Promise<void>;
}

export const DeckEditorHeader: React.FC<DeckEditorHeaderProps> = ({
  deck,
  onSaveTitle,
}) => {
  const t = useTranslation();
  const navigate = useNavigate();

  return (
    <>
      {/* Навигация */}
      <Link
        to="/decks"
        className="mb-6 inline-flex items-center text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        {t.decks.backToDecks}
      </Link>

      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-baseline gap-2 flex-1">
            <EditableText
              value={deck.name}
              onSave={onSaveTitle}
              placeholder={t.decks.deckNamePlaceholder}
              minLength={3}
              maxLength={100}
              inputClassName="text-2xl font-semibold"
              iconSize="h-5 w-5"
              iconHoverOpacity="group-hover:opacity-100"
              renderView={(v) => <h1 className="text-2xl font-semibold">{v}</h1>}
            />
            <span className="text-muted-foreground">({deck.words_count})</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/training/start?deck_id=${deck.id}`)}
            className="shrink-0"
          >
            <GraduationCap className="mr-1.5 h-4 w-4" />
            {t.trainingDashboard.train}
          </Button>
        </div>
      </div>
    </>
  );
};
