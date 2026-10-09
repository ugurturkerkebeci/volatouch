import { useEffect, useRef, useState, useCallback } from 'react';
import { ConnectionStatus, StreamSettings } from '../types';

interface UseStreamSocketProps {
  serverHost: string;
  initialSettings: StreamSettings;
}

export function useStreamSocket({ serverHost, initialSettings }: UseStreamSocketProps) {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [fps, setFps] = useState<number>(0);
  const [latency, setLatency] = useState<number>(0);
  const [settings, setSettings] = useState<StreamSettings>(initialSettings);
  
  const wsRef = useRef<WebSocket | null>(null);
  const currentBitmapRef = useRef<ImageBitmap | null>(null);
  const frameCountRef = useRef<number>(0);
  const lastFpsCalcRef = useRef<number>(performance.now());
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Connect to the binary stream websocket
  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus('connecting');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${serverHost}/ws/stream`;

    try {
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        setStatus('connected');
        ws.send(JSON.stringify({ type: 'set_quality', quality: settings.quality }));
        ws.send(JSON.stringify({ type: 'set_scale', scale: settings.scale }));
      };

      ws.onmessage = async (event: MessageEvent) => {
        if (event.data instanceof ArrayBuffer && event.data.byteLength > 8) {
          try {
            // Read 8-byte big-endian double timestamp
            const dataView = new DataView(event.data);
            const sendTs = dataView.getFloat64(0);
            const curLatency = Math.max(1, Math.round(Date.now() - sendTs));
            setLatency(curLatency);

            // Slice remaining buffer containing raw image bytes (JPEG from PC or PNG from Android)
            const imgBuffer = event.data.slice(8);
            const uint8 = new Uint8Array(imgBuffer, 0, 4);
            const isPng = uint8[0] === 0x89 && uint8[1] === 0x50 && uint8[2] === 0x4E && uint8[3] === 0x47;
            const mime = isPng ? 'image/png' : 'image/jpeg';
            const blob = new Blob([imgBuffer], { type: mime });
            const bitmap = await createImageBitmap(blob);
            
            // Swap bitmap ref and release previous GPU buffer
            const oldBitmap = currentBitmapRef.current;
            currentBitmapRef.current = bitmap;
            if (oldBitmap) {
              oldBitmap.close();
            }

            // Calculate FPS
            frameCountRef.current++;
            const now = performance.now();
            if (now - lastFpsCalcRef.current >= 1000) {
              setFps(Math.round((frameCountRef.current * 1000) / (now - lastFpsCalcRef.current)));
              frameCountRef.current = 0;
              lastFpsCalcRef.current = now;
            }
          } catch (err) {
            console.error('Frame decode error:', err);
          }
        }
      };

      ws.onerror = (e) => {
        console.warn('Stream WebSocket error:', e);
        setStatus('error');
      };

      ws.onclose = () => {
        setStatus('disconnected');
        wsRef.current = null;
        // Exponential/Fixed backoff reconnect
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, 2000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setStatus('error');
      reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
    }
  }, [serverHost, settings.quality, settings.scale]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (currentBitmapRef.current) {
        currentBitmapRef.current.close();
        currentBitmapRef.current = null;
      }
    };
  }, [connect]);

  // Dynamic settings update
  const updateSettings = useCallback((newSettings: Partial<StreamSettings>) => {
    setSettings((prev) => {
      const merged = { ...prev, ...newSettings };
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        if (newSettings.quality !== undefined) {
          wsRef.current.send(JSON.stringify({ type: 'set_quality', quality: newSettings.quality }));
        }
        if (newSettings.scale !== undefined) {
          wsRef.current.send(JSON.stringify({ type: 'set_scale', scale: newSettings.scale }));
        }
      }
      return merged;
    });
  }, []);

  return {
    status,
    fps,
    latency,
    settings,
    updateSettings,
    currentBitmapRef,
  };
}
