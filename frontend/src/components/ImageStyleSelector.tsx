import React from 'react';
import { ImageStyle } from '../types';

interface ImageStyleSelectorProps {
  value: ImageStyle;
  onChange: (style: ImageStyle) => void;
}

export const ImageStyleSelector: React.FC<ImageStyleSelectorProps> = ({
  value,
  onChange,
}) => {
  const styles: Array<{ id: ImageStyle; label: string; icon: string }> = [
    { id: 'minimalistic', label: 'Минималистичный', icon: '○' },
    { id: 'balanced', label: 'Сбалансированный', icon: '◐' },
    { id: 'creative', label: 'Творческий', icon: '◉' },
  ];

  const handleClick = (style: ImageStyle) => {
    onChange(style);
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Стиль изображений для колоды
      </label>
      <div className="flex gap-2">
        {styles.map((style) => (
          <button
            key={style.id}
            type="button"
            onClick={() => handleClick(style.id)}
            className={`
              flex-1 flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all
              ${
                value === style.id
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400 hover:bg-gray-50'
              }
            `}
            aria-label={style.label}
            title={style.label}
          >
            <span className="text-2xl mb-1">{style.icon}</span>
            <span className="text-xs font-medium">{style.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

