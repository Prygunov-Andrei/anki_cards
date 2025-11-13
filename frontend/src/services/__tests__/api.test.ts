import { apiService } from '../api';

// Mock axios
jest.mock('axios');

describe('ApiService', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should be defined', () => {
    expect(apiService).toBeDefined();
  });

  // Дополнительные тесты будут добавлены позже
});

