import React, { useRef, useEffect } from 'react';
import { ConnectionStatus } from '../types';

interface ScreenCanvasProps {
  currentBitmapRef: React.MutableRefObject<ImageBitmap | null>;
  status: ConnectionStatus;
  fps: number;
  inputMode: 'direct' | 'relative';
  scaleMode: 'fit' | 'fill';
  onDirectMove: (normX: number, normY: number) => void;
  onRelativeTouchStart: (e: TouchEvent) => void;
  onRelativeTouchMove: (e: TouchEvent) => void;
  onRelativeTouchEnd: (e: TouchEvent) => void;
  onMouseDown?: (button: 'left' | 'right') => void;
  onMouseUp?: (button: 'left' | 'right') => void;
  onMouseClick?: (button: 'left' | 'right') => void;
  onScroll?: (dy: number) => void;
  hostType?: 'windows' | 'android' | 'linux';
  onAndroidNav?: (action: 'back' | 'home' | 'recents' | 'power' | 'volume_up' | 'volume_down') => void;
}

export const ScreenCanvas: React.FC<ScreenCanvasProps> = ({
  currentBitmapRef,
  status,
  inputMode,
  scaleMode,
  onDirectMove,
  onRelativeTouchStart,
  onRelativeTouchMove,
  onRelativeTouchEnd,
  onMouseDown,
  onMouseUp,
  onMouseClick,
  onScroll,
  hostType,
  onAndroidNav,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isMouseDownRef = useRef<boolean>(false);
  
  // Track CSS bounds of rendered video image inside canvas
  const renderBoundsRef = useRef<{ offsetX: number; offsetY: number; width: number; height: number }>({
    offsetX: 0,
    offsetY: 0,
    width: 1,
    height: 1,
  });

  const canvasRectRef = useRef<{ left: number; top: number; width: number; height: number }>({
    left: 0,
    top: 0,
    width: window.innerWidth,
    height: window.innerHeight,
  });

  // Attach raw touch and mouse event listeners
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateRect = () => {
      const r = canvas.getBoundingClientRect();
      canvasRectRef.current = { left: r.left, top: r.top, width: r.width, height: r.height };
    };

    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('orientationchange', updateRect);
    document.addEventListener('fullscreenchange', updateRect);

    const getNormCoords = (clientX: number, clientY: number) => {
      const rect = canvasRectRef.current;
      const touchX = clientX - rect.left;
      const touchY = clientY - rect.top;
      const bounds = renderBoundsRef.current;
      const normX = Math.max(0, Math.min(1, (touchX - bounds.offsetX) / bounds.width));
      const normY = Math.max(0, Math.min(1, (touchY - bounds.offsetY) / bounds.height));
      return { normX, normY };
    };

    const handleCanvasTouchStart = (e: TouchEvent) => {
      e.preventDefault();
      updateRect();
      if (inputMode === 'direct') {
        const touch = e.touches[0];
        const { normX, normY } = getNormCoords(touch.clientX, touch.clientY);
        onDirectMove(normX, normY);
        onMouseDown?.('left');
      } else {
        onRelativeTouchStart(e);
      }
    };

    const handleCanvasTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      if (inputMode === 'direct') {
        const touch = e.touches[0];
        const { normX, normY } = getNormCoords(touch.clientX, touch.clientY);
        onDirectMove(normX, normY);
      } else {
        onRelativeTouchMove(e);
      }
    };

    const handleCanvasTouchEnd = (e: TouchEvent) => {
      e.preventDefault();
      if (inputMode === 'direct') {
        onMouseUp?.('left');
      } else {
        onRelativeTouchEnd(e);
      }
    };

    // Desktop Mouse Handlers
    const handleMouseDown = (e: MouseEvent) => {
      updateRect();
      const { normX, normY } = getNormCoords(e.clientX, e.clientY);
      onDirectMove(normX, normY);

      if (e.button === 0) {
        // Left button: press down
        isMouseDownRef.current = true;
        onMouseDown?.('left');
      } else if (e.button === 2) {
        // Right button
        e.preventDefault();
        if (hostType === 'android') {
          onAndroidNav?.('back');
        } else {
          onMouseClick?.('right');
        }
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const { normX, normY } = getNormCoords(e.clientX, e.clientY);
      onDirectMove(normX, normY);
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (e.button === 0 && isMouseDownRef.current) {
        isMouseDownRef.current = false;
        onMouseUp?.('left');
      }
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -1 : 1;
      onScroll?.(delta);
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
    };

    const opts = { passive: false };
    canvas.addEventListener('touchstart', handleCanvasTouchStart, opts);
    canvas.addEventListener('touchmove', handleCanvasTouchMove, opts);
    canvas.addEventListener('touchend', handleCanvasTouchEnd, opts);
    canvas.addEventListener('touchcancel', handleCanvasTouchEnd, opts);
    canvas.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel, opts);
    canvas.addEventListener('contextmenu', handleContextMenu);

    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('orientationchange', updateRect);
      document.removeEventListener('fullscreenchange', updateRect);
      canvas.removeEventListener('touchstart', handleCanvasTouchStart);
      canvas.removeEventListener('touchmove', handleCanvasTouchMove);
      canvas.removeEventListener('touchend', handleCanvasTouchEnd);
      canvas.removeEventListener('touchcancel', handleCanvasTouchEnd);
      canvas.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
      canvas.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [inputMode, hostType, onDirectMove, onRelativeTouchStart, onRelativeTouchMove, onRelativeTouchEnd, onMouseDown, onMouseUp, onMouseClick, onScroll, onAndroidNav]);

  // RequestAnimationFrame high-speed render loop
  useEffect(() => {
    let animId: number;

    const render = () => {
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
        const bitmap = currentBitmapRef.current;

        const dpr = window.devicePixelRatio || 1;
        const targetW = canvas.clientWidth * dpr;
        const targetH = canvas.clientHeight * dpr;

        if (canvas.width !== targetW || canvas.height !== targetH) {
          canvas.width = targetW;
          canvas.height = targetH;
        }

        if (ctx && bitmap) {
          if (scaleMode === 'fill') {
            // Fill mode: Stretch to 100% of the screen display with zero black bars
            renderBoundsRef.current = {
              offsetX: 0,
              offsetY: 0,
              width: canvas.clientWidth,
              height: canvas.clientHeight,
            };
            ctx.drawImage(bitmap, 0, 0, targetW, targetH);
          } else {
            // Fit mode: Maintain aspect ratio
            const hRatio = targetW / bitmap.width;
            const vRatio = targetH / bitmap.height;
            const ratio = Math.min(hRatio, vRatio);

            const drawW = bitmap.width * ratio;
            const drawH = bitmap.height * ratio;
            const shiftX = (targetW - drawW) / 2;
            const shiftY = (targetH - drawH) / 2;

            renderBoundsRef.current = {
              offsetX: shiftX / dpr,
              offsetY: shiftY / dpr,
              width: drawW / dpr,
              height: drawH / dpr,
            };

            ctx.fillStyle = '#020617';
            ctx.fillRect(0, 0, targetW, targetH);
            ctx.drawImage(
              bitmap,
              0,
              0,
              bitmap.width,
              bitmap.height,
              shiftX,
              shiftY,
              drawW,
              drawH
            );
          }
        } else if (ctx && status !== 'connected') {
          ctx.fillStyle = '#020617';
          ctx.fillRect(0, 0, targetW, targetH);
        }
      }
      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [currentBitmapRef, status, scaleMode]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-slate-950 flex items-center justify-center select-none touch-none">
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-default block select-none touch-none"
      />

      {status !== 'connected' && (
        <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-md flex flex-col items-center justify-center pointer-events-none p-6 text-center z-20">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-4" />
          <p className="text-lg font-bold text-slate-100">
            {status === 'connecting' ? 'Bilgisayara Baglaniliyor...' : 'Baglanti Kesildi'}
          </p>
          <p className="text-sm text-slate-400 mt-1 max-w-xs">
            Telefonunuzun bilgisayarla ayni Wi-Fi agina bagli oldugundan emin olun.
          </p>
        </div>
      )}
    </div>
  );
};
