import { useState, useRef, useCallback } from 'react';

export function useCamera() {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentFacingMode, setCurrentFacingMode] = useState<'user' | 'environment'>('environment');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async (facingMode: 'user' | 'environment' = 'environment') => {
    try {
      if (streamRef.current) {
        // Stop current stream if one exists
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      let stream: MediaStream | null = null;

      // Try high-resolution with advanced features first
      try {
        console.log(`Attempting high-resolution camera with facing mode: ${facingMode} and advanced features...`);
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode,
            width: { ideal: 3840 },
            height: { ideal: 2160 },
            // @ts-ignore - experimental features
            focusMode: { ideal: 'continuous' },
            zoom: { ideal: 2.0 }
          },
          audio: false,
        });
        console.log('✓ High-resolution camera activated');
      } catch (err) {
        console.warn('High-res with advanced features failed, trying basic high-res...', err);

        // Fallback: Try basic high-resolution without experimental features
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode,
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            },
            audio: false,
          });
          console.log('✓ Basic high-resolution camera activated');
        } catch (err2) {
          console.warn('Basic high-res failed, trying standard resolution...', err2);

          // Fallback: Try standard resolution
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode
            },
            audio: false,
          });
          console.log('✓ Standard resolution camera activated');
        }
      }

      if (stream && videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setCurrentFacingMode(facingMode);
        setIsActive(true);
        setError(null);

        // Log actual settings
        const track = stream.getVideoTracks()[0];
        const settings = track.getSettings();
        console.log('📹 Camera settings:', {
          width: settings.width,
          height: settings.height,
          facingMode: settings.facingMode,
          deviceId: settings.deviceId
        });

        // Wait for video to be ready
        videoRef.current.onloadedmetadata = () => {
          console.log('✓ Video stream ready:', {
            videoWidth: videoRef.current?.videoWidth,
            videoHeight: videoRef.current?.videoHeight
          });
        };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Camera access denied';
      setError(message);
      console.error('❌ Camera error:', err);
    }
  }, []);

  const switchCamera = useCallback(async () => {
    if (!isActive) {
      // If camera isn't active, start with the opposite facing mode
      const newFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
      await startCamera(newFacingMode);
      return;
    }

    // If camera is active, stop and restart with the opposite facing mode
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    const newFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
    await startCamera(newFacingMode);
  }, [isActive, currentFacingMode, startCamera]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  }, []);

  const captureImage = useCallback((): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current) {
        reject(new Error('Video not ready'));
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas not supported'));
        return;
      }

      ctx.drawImage(videoRef.current, 0, 0);
      const base64 = canvas.toDataURL('image/jpeg', 0.8);
      resolve(base64);
    });
  }, []);

  return {
    videoRef,
    isActive,
    error,
    currentFacingMode,
    startCamera,
    switchCamera,
    stopCamera,
    captureImage,
  };
}