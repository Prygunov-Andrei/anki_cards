import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, Loader2, ImageIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { useLanguage } from '../../contexts/LanguageContext';
import api from '../../services/api';
import { wordsService } from '../../services/words.service';

interface ImageUploadDialogProps {
  wordId: number;
  onUploaded: (imageUrl: string) => void;
  onClose: () => void;
}

/**
 * Диалог загрузки картинки для карточки.
 * Поддерживает drag-and-drop и file picker.
 */
export const ImageUploadDialog: React.FC<ImageUploadDialogProps> = ({
  wordId,
  onUploaded,
  onClose,
}) => {
  const { t } = useLanguage();
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const menu = t.trainingCard?.menu;

  const handleFile = useCallback((file: File) => {
    setError(null);

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      setError(menu?.invalidImageFormat || 'Only JPEG and PNG files are supported');
      return;
    }

    // Validate size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError(menu?.imageTooLarge || 'Image must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreview(url);
  }, [menu]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const uploadRes = await api.post<{ image_url: string; image_id: string }>(
        '/api/media/upload-image/',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      const uploadedUrl = uploadRes.data.image_url;

      // Link image to the word
      await wordsService.updateWord(wordId, { image_file: uploadedUrl } as any);

      onUploaded(uploadedUrl);
      onClose();
    } catch {
      setError(menu?.uploadError || 'Failed to upload image');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-card rounded-2xl shadow-xl p-6 w-96 max-w-[90vw] space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">
            {menu?.uploadImage || 'Upload image'}
          </h3>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          {preview ? (
            <div className="flex flex-col items-center gap-3">
              <img
                src={preview}
                alt="Preview"
                className="w-40 h-40 rounded-xl object-cover shadow-md"
              />
              <p className="text-sm text-muted-foreground">
                {selectedFile?.name}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 py-4">
              <ImageIcon className="h-12 w-12 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                {menu?.dragDropHint || 'Drag and drop an image here, or click to select'}
              </p>
              <p className="text-xs text-muted-foreground/60">
                JPEG, PNG · max 10MB
              </p>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            {menu?.cancel || 'Cancel'}
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="gap-2"
          >
            {isUploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {menu?.upload || 'Upload'}
          </Button>
        </div>
      </div>
    </div>
  );
};
