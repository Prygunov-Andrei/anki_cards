import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from '../ui/dropdown-menu';
import { Button } from '../ui/button';
import {
  MoreVertical,
  BookOpen,
  MessageSquare,
  Lightbulb,
  Users,
  Image,
  Mic,
  Upload,
  Trash2,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { aiGenerationService } from '../../services/ai-generation.service';
import { deckService } from '../../services/deck.service';
import type { CardListItem } from '../../types';
import type { WordDetail } from './TrainingCard';

interface TrainingCardMenuProps {
  card: CardListItem;
  wordDetail: WordDetail | null;
  onUpdateWordDetail: (cardId: number, updates: Partial<WordDetail>) => void;
  onUpdateCardMedia: (cardId: number, updates: { image_file?: string; audio_file?: string }) => void;
  onStartRecording: () => void;
  onStartImageUpload: () => void;
}

type GeneratingState = {
  etymology?: boolean;
  sentences?: boolean;
  hint?: boolean;
  synonym?: boolean;
  image?: boolean;
  audio?: boolean;
};

/**
 * Меню "три точки" на тренировочной карточке.
 * Позволяет генерировать/перегенерировать контент, загружать медиа, записывать аудио.
 */
export const TrainingCardMenu: React.FC<TrainingCardMenuProps> = ({
  card,
  wordDetail,
  onUpdateWordDetail,
  onUpdateCardMedia,
  onStartRecording,
  onStartImageUpload,
}) => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [generating, setGenerating] = useState<GeneratingState>({});

  const setGen = (key: keyof GeneratingState, val: boolean) => {
    setGenerating((prev) => ({ ...prev, [key]: val }));
  };

  const hasEtymology = !!wordDetail?.etymology;
  const hasSentences = wordDetail?.sentences && wordDetail.sentences.length > 0;
  const hasHint = !!wordDetail?.hint_text;
  const hasImage = !!card.image_file || !!wordDetail?.image_file || !!wordDetail?.image_url;
  const hasAudio = !!card.audio_file;

  // --- Handlers ---

  const handleGenerateEtymology = async () => {
    setGen('etymology', true);
    try {
      const res = await aiGenerationService.generateEtymology({
        word_id: card.word_id,
        force_regenerate: hasEtymology,
      });
      onUpdateWordDetail(card.id, { etymology: res.etymology });
    } catch {
      // Could show a toast here
    } finally {
      setGen('etymology', false);
    }
  };

  const handleGenerateSentences = async () => {
    setGen('sentences', true);
    try {
      const res = await aiGenerationService.generateSentences({
        word_id: card.word_id,
        count: 2,
      });
      const newSentences = res.sentences.map((s: string) => ({ text: s, source: 'ai' }));
      onUpdateWordDetail(card.id, {
        sentences: [...(wordDetail?.sentences || []), ...newSentences],
      });
    } catch {
      // Could show a toast here
    } finally {
      setGen('sentences', false);
    }
  };

  const handleGenerateHint = async () => {
    setGen('hint', true);
    try {
      const res = await aiGenerationService.generateHint({
        word_id: card.word_id,
        force_regenerate: hasHint,
      });
      onUpdateWordDetail(card.id, {
        hint_text: res.hint_text,
        hint_audio: res.hint_audio_url ?? undefined,
      });
    } catch {
      // Could show a toast here
    } finally {
      setGen('hint', false);
    }
  };

  const handleGenerateSynonym = async () => {
    setGen('synonym', true);
    try {
      await aiGenerationService.generateSynonym({
        word_id: card.word_id,
        create_card: true,
      });
    } catch {
      // Could show a toast here
    } finally {
      setGen('synonym', false);
    }
  };

  const handleGenerateImage = async (provider: 'openai' | 'gemini') => {
    setGen('image', true);
    try {
      const lang = wordDetail?.language || 'en';
      const res = await deckService.generateImage({
        word: card.word_text,
        translation: card.word_translation,
        language: lang,
        image_style: 'balanced',
        provider,
        word_id: card.word_id,
      });
      const newUrl = res.image_url;
      onUpdateCardMedia(card.id, { image_file: newUrl });
      onUpdateWordDetail(card.id, { image_file: newUrl, image_url: newUrl });
    } catch {
      // Could show a toast here
    } finally {
      setGen('image', false);
    }
  };

  const handleDeleteImage = async () => {
    try {
      // Set image to empty to clear it visually; backend update is via word
      onUpdateCardMedia(card.id, { image_file: '' });
      onUpdateWordDetail(card.id, { image_file: undefined, image_url: undefined });
    } catch {
      // Silent
    }
  };

  const handleGenerateAudio = async (provider: 'openai' | 'gtts') => {
    setGen('audio', true);
    try {
      const lang = wordDetail?.language || 'en';
      const res = await deckService.generateAudio({
        word: card.word_text,
        language: lang,
        provider,
        word_id: card.word_id,
      });
      const newUrl = res.audio_url;
      onUpdateCardMedia(card.id, { audio_file: newUrl });
    } catch {
      // Could show a toast here
    } finally {
      setGen('audio', false);
    }
  };

  const handleDeleteAudio = async () => {
    try {
      onUpdateCardMedia(card.id, { audio_file: '' });
    } catch {
      // Silent
    }
  };

  const handleOpenWord = () => {
    navigate(`/words/${card.word_id}`);
  };

  const isAnyGenerating = Object.values(generating).some(Boolean);

  const menu = t.trainingCard?.menu;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 flex-shrink-0"
          onClick={(e) => e.preventDefault()}
        >
          {isAnyGenerating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <MoreVertical className="h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {/* Etymology */}
        <DropdownMenuItem
          onClick={handleGenerateEtymology}
          disabled={generating.etymology}
        >
          <BookOpen className="mr-2 h-4 w-4" />
          {generating.etymology
            ? (menu?.generating || 'Generating...')
            : hasEtymology
              ? (menu?.regenerateEtymology || 'Regenerate etymology')
              : (menu?.generateEtymology || 'Generate etymology')}
        </DropdownMenuItem>

        {/* Sentences */}
        <DropdownMenuItem
          onClick={handleGenerateSentences}
          disabled={generating.sentences}
        >
          <MessageSquare className="mr-2 h-4 w-4" />
          {generating.sentences
            ? (menu?.generating || 'Generating...')
            : (menu?.sentences || 'Generate examples')}
        </DropdownMenuItem>

        {/* Hint */}
        <DropdownMenuItem
          onClick={handleGenerateHint}
          disabled={generating.hint}
        >
          <Lightbulb className="mr-2 h-4 w-4" />
          {generating.hint
            ? (menu?.generating || 'Generating...')
            : hasHint
              ? (menu?.hints || 'Regenerate hint')
              : (menu?.hints || 'Generate hint')}
        </DropdownMenuItem>

        {/* Synonym */}
        <DropdownMenuItem
          onClick={handleGenerateSynonym}
          disabled={generating.synonym}
        >
          <Users className="mr-2 h-4 w-4" />
          {generating.synonym
            ? (menu?.generating || 'Generating...')
            : (menu?.synonyms || 'Generate synonym')}
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Image submenu */}
        <DropdownMenuSub>
          <DropdownMenuSubTrigger disabled={generating.image}>
            <Image className="mr-2 h-4 w-4" />
            {generating.image
              ? (menu?.generating || 'Generating...')
              : (menu?.image || 'Image')}
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem onClick={() => handleGenerateImage('openai')}>
              {menu?.generateImage || 'Generate'} (OpenAI)
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleGenerateImage('gemini')}>
              {menu?.generateImage || 'Generate'} (Gemini)
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onStartImageUpload}>
              <Upload className="mr-2 h-4 w-4" />
              {menu?.uploadImage || 'Upload image'}
            </DropdownMenuItem>
            {hasImage && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleDeleteImage}
                  className="text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  {menu?.deleteImage || 'Delete image'}
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        {/* Audio submenu */}
        <DropdownMenuSub>
          <DropdownMenuSubTrigger disabled={generating.audio}>
            <Mic className="mr-2 h-4 w-4" />
            {generating.audio
              ? (menu?.generating || 'Generating...')
              : (menu?.audio || 'Audio')}
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem onClick={() => handleGenerateAudio('openai')}>
              {menu?.generateAudio || 'Generate'} (OpenAI)
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleGenerateAudio('gtts')}>
              {menu?.generateAudio || 'Generate'} (gTTS)
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onStartRecording}>
              <Mic className="mr-2 h-4 w-4" />
              {menu?.recordAudio || 'Record from microphone'}
            </DropdownMenuItem>
            {hasAudio && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleDeleteAudio}
                  className="text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  {menu?.deleteAudio || 'Delete audio'}
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        <DropdownMenuSeparator />

        {/* Open word detail */}
        <DropdownMenuItem onClick={handleOpenWord}>
          <ExternalLink className="mr-2 h-4 w-4" />
          {menu?.openWord || 'Open word'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
