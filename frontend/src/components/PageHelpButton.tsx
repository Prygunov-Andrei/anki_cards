import React, { useState, useEffect } from 'react';
import { HelpCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetTitle } from './ui/sheet';
import { useTranslation } from '../contexts/LanguageContext';

type HelpPageKey = keyof typeof import('../locales/ru').ru.help;

interface PageHelpButtonProps {
  pageKey: HelpPageKey;
}

/**
 * Contextual help button that appears in the bottom-right corner of each page.
 * Opens a slide-out panel with localized help content (steps + tips).
 */
export const PageHelpButton: React.FC<PageHelpButtonProps> = ({ pageKey }) => {
  const t = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [hasVisited, setHasVisited] = useState(false);

  const storageKey = `help_dismissed_${pageKey}`;
  const visitedKey = `help_visited_${pageKey}`;

  useEffect(() => {
    setIsDismissed(localStorage.getItem(storageKey) === 'true');
    setHasVisited(localStorage.getItem(visitedKey) === 'true');
  }, [storageKey, visitedKey]);

  const handleOpen = () => {
    setIsOpen(true);
    if (!hasVisited) {
      setHasVisited(true);
      localStorage.setItem(visitedKey, 'true');
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem(storageKey, 'true');
    setIsOpen(false);
  };

  const helpContent = t.help?.[pageKey];
  if (!helpContent || isDismissed) return null;

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={handleOpen}
        className="fixed bottom-6 right-6 z-40 h-11 w-11 rounded-full shadow-lg border-gray-300 bg-white/90 backdrop-blur-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-900/90 dark:hover:bg-gray-800"
        aria-label="Help"
      >
        <div className="relative">
          <HelpCircle className="h-5 w-5" />
          {!hasVisited && (
            <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-blue-500 animate-pulse" />
          )}
        </div>
      </Button>

      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="right" className="w-80 sm:w-96 overflow-y-auto">
          <SheetTitle className="text-lg font-semibold mb-4">
            {helpContent.title}
          </SheetTitle>

          {helpContent.steps.length > 0 && (
            <div className="mb-6">
              <ol className="space-y-3">
                {helpContent.steps.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm">
                    <span className="flex-shrink-0 flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 text-blue-700 text-xs font-medium dark:bg-blue-900/50 dark:text-blue-300">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 dark:text-gray-300 pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {helpContent.tips.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                {t.help.tipsTitle}
              </h3>
              <ul className="space-y-2">
                {helpContent.tips.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="flex-shrink-0 text-amber-500">*</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="w-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {t.help.dontShowAgain}
          </Button>
        </SheetContent>
      </Sheet>
    </>
  );
};
