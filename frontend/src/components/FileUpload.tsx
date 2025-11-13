import React, { useRef, useState } from 'react';

interface FileUploadProps {
  accept: string;
  maxSize: number; // в байтах
  onFileSelect: (file: File) => void;
  onRemove: () => void;
  currentFile?: File | null;
  label: string;
  error?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  maxSize,
  onFileSelect,
  onRemove,
  currentFile,
  label,
  error,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [localError, setLocalError] = useState<string>('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Валидация размера
    if (file.size > maxSize) {
      const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(1);
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setLocalError(`Файл слишком большой. Максимум: ${maxSizeMB}MB, ваш файл: ${fileSizeMB}MB`);
      return;
    }

    // Валидация формата
    const acceptedTypes = accept.split(',').map((t) => t.trim());
    const fileType = file.type || '';
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    const isValidType =
      acceptedTypes.some((type) => fileType.includes(type.replace('*', ''))) ||
      acceptedTypes.some((type) => type.includes(fileExtension));

    if (!isValidType) {
      setLocalError(`Неподдерживаемый формат файла. Разрешены: ${accept}`);
      return;
    }

    setLocalError('');
    onFileSelect(file);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemove = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setLocalError('');
    onRemove();
  };

  const displayError = error || localError;

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          type="button"
          onClick={handleClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
        >
          Выбрать файл
        </button>
        {currentFile && (
          <>
            <span className="text-sm text-gray-600 truncate max-w-xs">{currentFile.name}</span>
            <button
              type="button"
              onClick={handleRemove}
              className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
            >
              Удалить
            </button>
          </>
        )}
      </div>
      {displayError && <p className="text-sm text-red-600">{displayError}</p>}
    </div>
  );
};

