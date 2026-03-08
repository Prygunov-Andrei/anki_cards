import { describe, it, expect } from 'vitest';
import {
  mediaModelToBackend,
  backendToMediaModel,
  getMediaModelCost,
} from '../MediaModelSelector';

describe('mediaModelToBackend', () => {
  it('maps dalle3 to openai provider', () => {
    const result = mediaModelToBackend('dalle3');
    expect(result.image_provider).toBe('openai');
  });

  it('maps gemini-flash to gemini provider with flash model', () => {
    const result = mediaModelToBackend('gemini-flash');
    expect(result.image_provider).toBe('gemini');
    expect(result.gemini_model).toBe('gemini-2.5-flash-image');
  });

  it('maps nano-banana to gemini provider with 3.1 model', () => {
    const result = mediaModelToBackend('nano-banana');
    expect(result.image_provider).toBe('gemini');
    expect(result.gemini_model).toBe('gemini-3.1-flash-image-preview');
  });
});

describe('backendToMediaModel', () => {
  it('maps openai provider to dalle3', () => {
    expect(backendToMediaModel('openai', 'gemini-2.5-flash-image')).toBe('dalle3');
  });

  it('maps gemini + flash model to gemini-flash', () => {
    expect(backendToMediaModel('gemini', 'gemini-2.5-flash-image')).toBe('gemini-flash');
  });

  it('maps gemini + 3.1 model to nano-banana', () => {
    expect(backendToMediaModel('gemini', 'gemini-3.1-flash-image-preview')).toBe('nano-banana');
  });

  it('openai provider ignores gemini_model value', () => {
    expect(backendToMediaModel('openai', 'gemini-3.1-flash-image-preview')).toBe('dalle3');
  });
});

describe('getMediaModelCost', () => {
  it('dalle3 costs 1 token', () => {
    expect(getMediaModelCost('dalle3')).toBe(1);
  });

  it('gemini-flash costs 0.5 tokens', () => {
    expect(getMediaModelCost('gemini-flash')).toBe(0.5);
  });

  it('nano-banana costs 1 token', () => {
    expect(getMediaModelCost('nano-banana')).toBe(1);
  });
});
