import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Deck } from '../types';
import { Card } from './ui/card';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from './ui/dropdown-menu';
import { MoreVertical, Edit, Trash2, BookOpen, Calendar, Download, Merge, ArrowLeftRight, FileText, GraduationCap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru, enUS, de, es, fr, it, ptBR } from 'date-fns/locale';
import { getAbsoluteUrl } from '../utils/url-helpers';
import { useTranslation, useLanguage } from '../contexts/LanguageContext';

interface DeckCardProps {
  deck: Deck;
  onEdit: (deck: Deck) => void;
  onDelete: (deck: Deck) => void;
  onGenerateApkg: (deck: Deck) => void;
  onMerge?: (sourceDeckId: number, targetDeckId: number) => void;
  onInvertAll?: (deck: Deck) => void;
  onCreateEmptyCards?: (deck: Deck) => void;
  availableDecks?: Deck[];
}

/**
 * Компонент DeckCard - карточка колоды
 */
export const DeckCard: React.FC<DeckCardProps> = ({
  deck,
  onEdit,
  onDelete,
  onGenerateApkg,
  onMerge,
  onInvertAll,
  onCreateEmptyCards,
  availableDecks,
}) => {
  const t = useTranslation();
  const { locale } = useLanguage();
  const navigate = useNavigate();
  
  // Мапинг языков на локали date-fns
  const dateLocales = {
    ru,
    en: enUS,
    de,
    es,
    fr,
    it,
    pt: ptBR,
  };
  
  const currentLocale = dateLocales[locale as keyof typeof dateLocales] || enUS;

  // Форматирование даты обновления
  const getRelativeTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: currentLocale,
      });
    } catch {
      return t.decks.recently;
    }
  };
  
  // Плюрализация слов
  const getWordsText = (count: number) => {
    if (locale === 'ru') {
      if (count === 1) return t.decks.word;
      if (count >= 2 && count <= 4) return t.decks.wordsTwo;
      return t.decks.words;
    }
    // Для других языков
    return count === 1 ? t.decks.word : t.decks.words;
  };
  
  // Плюрализация карточек
  const getCardsText = (count: number) => {
    if (locale === 'ru') {
      if (count === 1) return t.decks.card;
      if (count >= 2 && count <= 4) return t.decks.cardsTwo;
      return t.decks.cards;
    }
    // Для других языков
    return count === 1 ? t.decks.card : t.decks.cards;
  };

  return (
    <Card className="group relative overflow-hidden transition-all hover:shadow-lg dark:hover:shadow-cyan-500/10">
      {/* Контент карточки */}
      <Link to={`/decks/${deck.id}`} className="block">
        <div className="p-5">
          {/* Название колоды с меню */}
          <div className="mb-4 flex items-start justify-between gap-2">
            <h3 className="line-clamp-2 flex-1 text-gray-900 transition-colors group-hover:text-blue-600 dark:text-gray-100 dark:group-hover:text-blue-400">
              {deck.name}
            </h3>

            {/* Меню действий */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                  onClick={(e) => e.preventDefault()}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  navigate(`/training/start?deck_id=${deck.id}`);
                }}>
                  <GraduationCap className="mr-2 h-4 w-4" />
                  {t.trainingDashboard.train}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onEdit(deck);
                }}>
                  <Edit className="mr-2 h-4 w-4" />
                  {t.decks.editDeck}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onGenerateApkg(deck);
                }}>
                  <Download className="mr-2 h-4 w-4" />
                  {t.decks.generateApkg}
                </DropdownMenuItem>
                
                {onMerge && availableDecks && availableDecks.length > 0 && (
                  <DropdownMenuSub>
                    <DropdownMenuSubTrigger>
                      <Merge className="mr-2 h-4 w-4" />
                      {t.decks.mergeWith}
                    </DropdownMenuSubTrigger>
                    <DropdownMenuSubContent>
                      {availableDecks.map((availableDeck) => (
                        <DropdownMenuItem
                          key={availableDeck.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            onMerge(deck.id, availableDeck.id);
                          }}
                        >
                          <div className="flex items-center justify-between w-full">
                            <span className="flex-1 truncate">{availableDeck.name}</span>
                            <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                              {availableDeck.words_count} {getWordsText(availableDeck.words_count)}
                            </span>
                          </div>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuSub>
                )}
                
                {onInvertAll && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      onInvertAll(deck);
                    }}
                  >
                    <ArrowLeftRight className="mr-2 h-4 w-4" />
                    {t.words.invertAllWords}
                  </DropdownMenuItem>
                )}
                
                {onCreateEmptyCards && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      onCreateEmptyCards(deck);
                    }}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    {t.words.createEmptyCards}
                  </DropdownMenuItem>
                )}
                
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    onDelete(deck);
                  }}
                  className="text-red-600 focus:text-red-700"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  {t.common.delete}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Метаинформация */}
          <div className="space-y-2">
            {/* Количество слов и карточек */}
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <BookOpen className="mr-2 h-4 w-4 text-cyan-500" />
              <span>
                {deck.unique_words_count !== undefined && deck.unique_words_count !== deck.words_count ? (
                  <>
                    {deck.unique_words_count} {getWordsText(deck.unique_words_count)} ({deck.words_count} {getCardsText(deck.words_count)})
                  </>
                ) : (
                  <>
                    {deck.words_count} {getWordsText(deck.words_count)}
                  </>
                )}
              </span>
            </div>

            {/* Дата создания и обновления */}
            <div className="space-y-1">
              {/* Дата создания */}
              <div className="flex items-center text-sm text-gray-500 dark:text-gray-500">
                <Calendar className="mr-2 h-4 w-4" />
                <span>{t.decks.created} {getRelativeTime(deck.created_at)}</span>
              </div>
              {/* Дата обновления (показываем только если отличается от создания более чем на 1 секунду) */}
              {(() => {
                const createdTime = new Date(deck.created_at).getTime();
                const updatedTime = new Date(deck.updated_at).getTime();
                const diffSeconds = Math.abs(updatedTime - createdTime) / 1000;
                // Показываем дату обновления, если разница больше 1 секунды
                return diffSeconds > 1;
              })() && (
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-500">
                  <Calendar className="mr-2 h-4 w-4" />
                  <span>{t.decks.updated} {getRelativeTime(deck.updated_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </Link>
    </Card>
  );
};