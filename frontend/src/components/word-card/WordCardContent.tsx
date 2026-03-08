import React from 'react';
import { EditableText } from '../EditableText';
import { displayWord } from '../../utils/helpers';

interface WordCardContentProps {
  word: string;
  translation: string;
  wordId?: number;
  onWordUpdate?: (wordId: number, data: { original_word?: string; translation?: string }) => Promise<void>;
}

export const WordCardContent: React.FC<WordCardContentProps> = ({
  word,
  translation,
  wordId,
  onWordUpdate,
}) => {
  return (
    <div className="space-y-1">
      {wordId && onWordUpdate ? (
        <>
          <div>
            <EditableText
              value={word}
              onSave={async (newWord) => {
                await onWordUpdate(wordId, { original_word: newWord });
              }}
              className="font-semibold text-lg text-gray-900 dark:text-gray-100"
              inputClassName="font-semibold text-lg"
            />
          </div>
          <div>
            <EditableText
              value={translation}
              onSave={async (newTranslation) => {
                await onWordUpdate(wordId, { translation: newTranslation });
              }}
              className="text-sm text-muted-foreground"
              inputClassName="text-sm"
            />
          </div>
        </>
      ) : (
        <>
          <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">
            {displayWord(word)}
          </h3>
          <p className="text-sm text-muted-foreground">
            {translation}
          </p>
        </>
      )}
    </div>
  );
};
