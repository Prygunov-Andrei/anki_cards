import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from '../contexts/LanguageContext';
import { libraryService, LiteraryTextDetail } from '../services/library.service';
import { WordPopup } from '../components/reader/WordPopup';
import { ArrowLeft, Languages, Type } from 'lucide-react';

const FONT_SIZES = ['text-sm', 'text-base', 'text-lg'] as const;
const FONT_SIZE_LABELS = ['S', 'M', 'L'];

const ReaderPage: React.FC = () => {
  const { sourceSlug, textSlug } = useParams<{ sourceSlug: string; textSlug: string }>();
  const navigate = useNavigate();
  const t = useTranslation();

  const [text, setText] = useState<LiteraryTextDetail | null>(null);
  const [language, setLanguage] = useState<string>('de');
  const [loading, setLoading] = useState(true);
  const [fontSizeIdx, setFontSizeIdx] = useState(() => {
    const saved = localStorage.getItem('reader_font_size');
    return saved ? parseInt(saved, 10) : 1;
  });

  // Word popup state
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });

  // Scroll progress
  const [scrollProgress, setScrollProgress] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sourceSlug || !textSlug) return;
    setLoading(true);
    libraryService
      .getText(sourceSlug, textSlug, language)
      .then(setText)
      .catch(() => {
        // If requested language not available, try the other
        const fallback = language === 'de' ? 'ru' : 'de';
        libraryService.getText(sourceSlug, textSlug, fallback).then((t) => {
          setText(t);
          setLanguage(fallback);
        }).catch(() => navigate('/library'));
      })
      .finally(() => setLoading(false));
  }, [sourceSlug, textSlug, language, navigate]);

  // Scroll progress tracker
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(docHeight > 0 ? Math.min(scrollTop / docHeight, 1) : 0);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleFontSize = () => {
    const next = (fontSizeIdx + 1) % FONT_SIZES.length;
    setFontSizeIdx(next);
    localStorage.setItem('reader_font_size', String(next));
  };

  const handleWordClick = useCallback((e: React.MouseEvent, token: string) => {
    // Clean the token - remove punctuation from edges
    const cleaned = token.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '');
    if (!cleaned || cleaned.length < 2) return;

    setSelectedWord(cleaned);
    setPopupPosition({ x: e.clientX, y: e.clientY });
  }, []);

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === 'de' ? 'ru' : 'de'));
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="mt-6 space-y-3">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-5 animate-pulse rounded bg-muted" style={{ width: `${70 + Math.random() * 30}%` }} />
          ))}
        </div>
      </div>
    );
  }

  if (!text) return null;

  // Split text into clickable word spans
  const renderText = (fullText: string) => {
    const paragraphs = fullText.split('\n');
    return paragraphs.map((para, pIdx) => {
      if (!para.trim()) return <br key={pIdx} />;

      const tokens = para.split(/(\s+)/);
      return (
        <p key={pIdx} className="mb-4 leading-relaxed">
          {tokens.map((token, tIdx) => {
            const isWord = /\p{L}/u.test(token);
            if (!isWord) return <span key={tIdx}>{token}</span>;

            return (
              <span
                key={tIdx}
                onClick={(e) => handleWordClick(e, token)}
                className="cursor-pointer rounded-sm transition-colors hover:bg-yellow-200/60 dark:hover:bg-yellow-500/20"
              >
                {token}
              </span>
            );
          })}
        </p>
      );
    });
  };

  return (
    <div className="relative">
      {/* Scroll progress bar */}
      <div className="fixed left-0 right-0 top-0 z-30 h-0.5 bg-muted">
        <div
          className="h-full bg-primary transition-[width] duration-150"
          style={{ width: `${scrollProgress * 100}%` }}
        />
      </div>

      {/* Header toolbar */}
      <div className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-2xl items-center gap-2 px-4 py-2">
          <button
            onClick={() => navigate('/library')}
            className="rounded-lg p-2 hover:bg-muted"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{text.title}</p>
          </div>

          {/* Language toggle */}
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <Languages className="h-3.5 w-3.5" />
            {language.toUpperCase()}
          </button>

          {/* Font size */}
          <button
            onClick={handleFontSize}
            className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <Type className="h-3.5 w-3.5" />
            {FONT_SIZE_LABELS[fontSizeIdx]}
          </button>
        </div>
      </div>

      {/* Text content */}
      <div ref={contentRef} className="mx-auto max-w-2xl px-4 py-6">
        <div className={`${FONT_SIZES[fontSizeIdx]} text-foreground`}>
          {renderText(text.full_text)}
        </div>

        {/* End marker */}
        <div className="my-12 text-center text-muted-foreground">
          <p className="text-sm">- - -</p>
        </div>
      </div>

      {/* Word popup */}
      {selectedWord && sourceSlug && (
        <WordPopup
          word={selectedWord}
          position={popupPosition}
          sourceSlug={sourceSlug}
          onClose={() => setSelectedWord(null)}
        />
      )}
    </div>
  );
};

export default ReaderPage;
