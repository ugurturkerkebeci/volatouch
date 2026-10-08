import { useRef, useState, useCallback, useEffect } from 'react';
import { TouchpadSettings } from '../types';

interface TouchPoint {
  x: number;
  y: number;
}

interface UseTouchEngineProps {
  serverHost: string;
  settings: TouchpadSettings;
}

export function useTouchEngine({ serverHost, settings }: UseTouchEngineProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isRightClickMode, setIsRightClickMode] = useState<boolean>(false);
  const isRightClickModeRef = useRef<boolean>(false);

  // Sync ref with state
  useEffect(() => {
    isRightClickModeRef.current = isRightClickMode;
  }, [isRightClickMode]);

  // Gesture state tracking
  const touchStartTimeRef = useRef<number>(0);
  const touchStartPosRef = useRef<TouchPoint>({ x: 0, y: 0 });
  const prevTouchPosRef = useRef<TouchPoint>({ x: 0, y: 0 });
  const prevTwoTouchPosRef = useRef<[TouchPoint, TouchPoint] | null>(null);
  const totalMovementRef = useRef<number>(0);
  const touchCountRef = useRef<number>(0);
  
  // Long-press timer for drag & drop
  const longPressTimerRef = useRef<number | null>(null);
  const isDraggingRef = useRef<boolean>(false);

  // Establish input WebSocket connection
  const connectInputSocket = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${serverHost}/ws/input`);

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      setTimeout(connectInputSocket, 2000);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    wsRef.current = ws;
  }, [serverHost]);

  useEffect(() => {
    connectInputSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectInputSocket]);

  const sendCommand = useCallback((cmd: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(cmd));
    }
  }, []);

  // Direct Mouse Click action (for dedicated on-screen Left/Right Click pads)
  const sendMouseClick = useCallback((button: 'left' | 'right' | 'middle' = 'left', count: number = 1) => {
    sendCommand({ type: 'mouse_click', button, clicks: count });
    if ('vibrate' in navigator) {
      try { navigator.vibrate(button === 'right' ? [20, 30, 20] : 15); } catch (_) {}
    }
  }, [sendCommand]);

  const sendMouseMoveAbs = useCallback((normX: number, normY: number) => {
    sendCommand({ type: 'mouse_move_abs', norm_x: normX, norm_y: normY });
  }, [sendCommand]);

  const sendMouseDown = useCallback((button: 'left' | 'right' = 'left') => {
    sendCommand({ type: 'mouse_down', button });
  }, [sendCommand]);

  const sendMouseUp = useCallback((button: 'left' | 'right' = 'left') => {
    sendCommand({ type: 'mouse_up', button });
  }, [sendCommand]);

  // Direct Mouse Scroll action (for dedicated on-screen scroll bar)
  const sendScroll = useCallback((dy: number) => {
    sendCommand({ type: 'mouse_scroll', dx: 0, dy });
  }, [sendCommand]);

  // Keyboard and Hardware control dispatchers
  const sendKeyTap = useCallback((key: string, modifiers: string[] = []) => {
    sendCommand({ type: 'key_tap', key, modifiers });
  }, [sendCommand]);

  const sendKeyDown = useCallback((key: string) => {
    sendCommand({ type: 'key_down', key });
  }, [sendCommand]);

  const sendKeyUp = useCallback((key: string) => {
    sendCommand({ type: 'key_up', key });
  }, [sendCommand]);

  const sendTextInput = useCallback((text: string) => {
    sendCommand({ type: 'text_input', text });
  }, [sendCommand]);

  const clearLongPressTimer = () => {
    if (longPressTimerRef.current !== null) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  };

  // Touch Event Handlers
  const handleTouchStart = useCallback((e: TouchEvent) => {
    e.preventDefault();
    clearLongPressTimer();

    const touches = e.touches;
    touchCountRef.current = touches.length;
    touchStartTimeRef.current = performance.now();
    totalMovementRef.current = 0;

    if (touches.length === 1) {
      const touch = touches[0];
      const pos = { x: touch.clientX, y: touch.clientY };
      touchStartPosRef.current = pos;
      prevTouchPosRef.current = pos;

      // Start long-press detection timer (380ms) for Drag & Drop
      longPressTimerRef.current = window.setTimeout(() => {
        if (totalMovementRef.current < 18 && touchCountRef.current === 1) {
          isDraggingRef.current = true;
          setIsDragging(true);
          if ('vibrate' in navigator) {
            try { navigator.vibrate(40); } catch (_) {}
          }
          sendCommand({ type: 'mouse_down', button: 'left' });
        }
      }, 380);

    } else if (touches.length === 2) {
      clearLongPressTimer();
      prevTwoTouchPosRef.current = [
        { x: touches[0].clientX, y: touches[0].clientY },
        { x: touches[1].clientX, y: touches[1].clientY }
      ];
    }
  }, [sendCommand]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    e.preventDefault();
    const touches = e.touches;

    if (touches.length === 1) {
      const touch = touches[0];
      const curX = touch.clientX;
      const curY = touch.clientY;
      const prev = prevTouchPosRef.current;

      const rawDx = curX - prev.x;
      const rawDy = curY - prev.y;
      prevTouchPosRef.current = { x: curX, y: curY };

      const dist = Math.hypot(rawDx, rawDy);
      totalMovementRef.current += dist;

      if (totalMovementRef.current > 15 && !isDraggingRef.current) {
        clearLongPressTimer();
      }

      // Smooth acceleration curve
      const accelFactor = 1 + dist * settings.acceleration;
      const finalDx = rawDx * settings.sensitivity * accelFactor;
      const finalDy = rawDy * settings.sensitivity * accelFactor;

      sendCommand({
        type: 'mouse_move',
        dx: finalDx,
        dy: finalDy
      });

    } else if (touches.length === 2 && prevTwoTouchPosRef.current) {
      clearLongPressTimer();
      const [t1, t2] = [touches[0], touches[1]];
      const [prev1, prev2] = prevTwoTouchPosRef.current;

      const dy1 = t1.clientY - prev1.y;
      const dy2 = t2.clientY - prev2.y;
      const avgDy = (dy1 + dy2) / 2;

      prevTwoTouchPosRef.current = [
        { x: t1.clientX, y: t1.clientY },
        { x: t2.clientX, y: t2.clientY }
      ];

      totalMovementRef.current += Math.abs(avgDy);

      if (Math.abs(avgDy) > 0.5) {
        // Natural scroll wheel
        const scrollDelta = (avgDy / 2.5) * settings.scrollSensitivity;
        sendCommand({
          type: 'mouse_scroll',
          dx: 0,
          dy: scrollDelta
        });
      }
    }
  }, [sendCommand, settings]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    e.preventDefault();
    clearLongPressTimer();

    const elapsed = performance.now() - touchStartTimeRef.current;
    const moved = totalMovementRef.current;
    const initialFingers = touchCountRef.current;

    if (isDraggingRef.current) {
      isDraggingRef.current = false;
      setIsDragging(false);
      sendCommand({ type: 'mouse_up', button: 'left' });
      if ('vibrate' in navigator) {
        try { navigator.vibrate(25); } catch (_) {}
      }
    } else if (moved < 20 && elapsed < 320) {
      // Tap detection
      if (initialFingers === 1) {
        if (isRightClickModeRef.current) {
          // If Right-Click Sticky Mode is active, tap acts as Right Click!
          sendCommand({ type: 'mouse_click', button: 'right', clicks: 1 });
          setIsRightClickMode(false);
          if ('vibrate' in navigator) {
            try { navigator.vibrate([20, 30, 20]); } catch (_) {}
          }
        } else {
          // Normal 1-finger tap -> Left Click
          sendCommand({ type: 'mouse_click', button: 'left', clicks: 1 });
          if ('vibrate' in navigator) {
            try { navigator.vibrate(18); } catch (_) {}
          }
        }
      } else if (initialFingers === 2) {
        // 2-finger tap -> Right Click
        sendCommand({ type: 'mouse_click', button: 'right', clicks: 1 });
        if ('vibrate' in navigator) {
          try { navigator.vibrate([20, 35, 20]); } catch (_) {}
        }
      }
    }

    touchCountRef.current = e.touches.length;
    if (e.touches.length === 0) {
      prevTwoTouchPosRef.current = null;
    }
  }, [sendCommand]);

  return {
    isConnected,
    isDragging,
    isRightClickMode,
    setIsRightClickMode,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    sendMouseClick,
    sendMouseDown,
    sendMouseUp,
    sendMouseMoveAbs,
    sendScroll,
    sendKeyTap,
    sendKeyDown,
    sendKeyUp,
    sendTextInput,
  };
}
