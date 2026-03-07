import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../contexts/LanguageContext';
import { libraryService, LiteraryTextListItem } from '../services/library.service';
import { literaryContextService } from '../services/literary-context.service';
import { LiterarySource } from '../types/literary-context';
import { Search, BookOpen, ChevronRight, Globe, SortAsc } from 'lucide-react';
import { PageHelpButton } from '../components/PageHelpButton';

const LibraryPage: React.FC = () => {
  const t = useTranslation();
  const navigate = useNavigate();
  const [sources, setSources] = useState<LiterarySource[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [texts, setTexts] = useState<LiteraryTextListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('sort_order');

  useEffect(() => {
    literaryContextService
      .getSources()
      .then((s) => {
        setSources(s);
        if (s.length > 0) setSelectedSource(s[0].slug);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedSource) return;
    setLoading(true);
    libraryService
      .getTexts(selectedSource, { search, sort })
      .then(setTexts)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedSource, search, sort]);

  if (loading && sources.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/40" />
        <p className="mt-4 text-muted-foreground">{t.library?.empty || 'No literary sources available'}</p>
      </div>
    );
  }

  const hasGerman = (item: LiteraryTextListItem) => item.languages.includes('de');

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="text-2xl font-bold">{t.library?.title || 'Library'}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {texts.length} {t.library?.stories || 'stories'}
        {texts.filter(hasGerman).length < texts.length && (
          <span> ({texts.filter(hasGerman).length} {t.library?.translated || 'translated'})</span>
        )}
      </p>

      {/* Search + Sort */}
      <div className="mt-4 flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.library?.search || 'Search stories...'}
            className="w-full rounded-xl border bg-background py-2.5 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="rounded-xl border bg-background px-3 py-2.5 text-sm outline-none"
        >
          <option value="sort_order">#</option>
          <option value="title">A-Z</option>
          <option value="word_count">{t.library?.byLength || 'Length'}</option>
        </select>
      </div>

      {/* Stories list */}
      <div className="mt-4 space-y-2">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-muted" />
          ))
        ) : (
          texts.map((text) => (
            <button
              key={text.slug}
              onClick={() => {
                if (hasGerman(text)) {
                  navigate(`/library/${selectedSource}/${text.slug}`);
                }
              }}
              disabled={!hasGerman(text)}
              className={`
                flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-colors
                ${hasGerman(text)
                  ? 'hover:bg-muted/50 active:bg-muted'
                  : 'opacity-40 cursor-not-allowed'
                }
              `}
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{text.title}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{text.word_count.toLocaleString()} {t.library?.words || 'words'}</span>
                  <span className="flex items-center gap-0.5">
                    <Globe className="h-3 w-3" />
                    {text.languages.join(', ')}
                  </span>
                </div>
              </div>
              {hasGerman(text) && (
                <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground" />
              )}
            </button>
          ))
        )}
      </div>

      <PageHelpButton pageKey="library" />
    </div>
  );
};

export default LibraryPage;
