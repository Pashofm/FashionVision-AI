import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import useCamera from '../../hooks/useCamera';

describe('useCamera Hook', () => {
  const mockVideoRef = { current: null };
  const mockStream = {
    getTracks: vi.fn(() => [
      { stop: vi.fn() },
      { stop: vi.fn() }
    ])
  };

  beforeEach(() => {
    vi.clearAllMocks();
    global.navigator.mediaDevices = {
      getUserMedia: vi.fn(() => Promise.resolve(mockStream))
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have initial state with no stream', () => {
      const { result } = renderHook(() => useCamera());
      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('openCamera', () => {
    it('should be a function', () => {
      const { result } = renderHook(() => useCamera());
      expect(typeof result.current.openCamera).toBe('function');
    });

    it('should request camera access with rear camera preference', async () => {
      const { result } = renderHook(() => useCamera());

      await result.current.openCamera();

      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
        video: { facingMode: 'environment' }
      });
    });

    it('should set stream when camera opens successfully', async () => {
      const { result } = renderHook(() => useCamera());

      await result.current.openCamera();

      expect(result.current.stream).toBe(mockStream);
      expect(result.current.isActive).toBe(true);
    });

    it('should set error when camera access is denied', async () => {
      const deniedError = new Error('Camera access denied');
      navigator.mediaDevices.getUserMedia.mockRejectedValueOnce(deniedError);

      const { result } = renderHook(() => useCamera());

      await result.current.openCamera();

      expect(result.current.error).toBe('Camera access denied');
      expect(result.current.isActive).toBe(false);
    });
  });

  describe('closeCamera', () => {
    it('should be a function', () => {
      const { result } = renderHook(() => useCamera());
      expect(typeof result.current.closeCamera).toBe('function');
    });

    it('should stop all tracks when closing', async () => {
      const { result } = renderHook(() => useCamera());

      await result.current.openCamera();
      await result.current.closeCamera();

      expect(mockStream.getTracks()).toHaveBeenCalled();
      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
    });

    it('should handle closing when no stream is active', async () => {
      const { result } = renderHook(() => useCamera());

      await result.current.closeCamera();

      expect(result.current.isActive).toBe(false);
    });
  });

  describe('captureFrame', () => {
    it('should be a function', () => {
      const { result } = renderHook(() => useCamera());
      expect(typeof result.current.captureFrame).toBe('function');
    });

    it('should return null when video ref is not set', async () => {
      const { result } = renderHook(() => useCamera());

      const frame = await result.current.captureFrame(null);
      expect(frame).toBeNull();
    });

    it('should draw video frame to canvas and return data URL', async () => {
      const mockCanvas = {
        getContext: vi.fn(() => ({
          drawImage: vi.fn()
        })),
        toDataURL: vi.fn(() => 'data:image/png;base64,mockdata')
      };

      const mockVideo = {
        videoWidth: 640,
        videoHeight: 480,
        width: 640,
        height: 480
      };

      const { result } = renderHook(() => useCamera());

      const frame = await result.current.captureFrame(mockCanvas, mockVideo);

      expect(mockCanvas.getContext).toHaveBeenCalledWith('2d');
      expect(mockCanvas.toDataURL).toHaveBeenCalled();
    });
  });
});

import { renderHook } from '@testing-library/react';
