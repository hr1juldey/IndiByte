import { io, Socket } from 'socket.io-client';
import type {
  ScanProgressEvent,
  DetailedAssessment,
  OnboardingQuestionEvent,
  ScanErrorEvent
} from '../types';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000';

class SocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect() {
    if (this.socket?.connected) {
      console.log('Socket already connected');
      return;
    }

    this.socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('✓ Connected to server');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.warn('✗ Disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      this.reconnectAttempts++;
      console.error('Connection error:', error.message);

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        throw new Error('Cannot connect to server. Please check backend is running.');
      }
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  // Scan events
  onScanStarted(callback: (data: { scan_id: string }) => void) {
    this.socket?.on('scan_started', callback);
  }

  onScanProgress(callback: (data: ScanProgressEvent) => void) {
    this.socket?.on('scan_progress', callback);
  }

  onScanComplete(callback: (data: { detailed_assessment: DetailedAssessment }) => void) {
    this.socket?.on('scan_complete', callback);
  }

  onScanError(callback: (data: ScanErrorEvent) => void) {
    this.socket?.on('scan_error', callback);
  }

  // Emit scan request
  startScan(userName: string, imageBase64: string) {
    if (!this.socket?.connected) {
      throw new Error('Not connected to server');
    }

    this.socket.emit('start_scan', {
      user_name: userName,
      image_base64: imageBase64,
      source: 'camera',
    });
  }

  // Onboarding events
  onOnboardingQuestion(callback: (data: OnboardingQuestionEvent) => void) {
    this.socket?.on('onboarding_question', callback);
  }

  startOnboarding(userName: string) {
    this.socket?.emit('start_onboarding', { user_name: userName });
  }

  sendOnboardingResponse(questionNumber: number, response: string) {
    this.socket?.emit('onboarding_response', {
      question_number: questionNumber,
      response,
    });
  }
}

export const socketManager = new SocketManager();