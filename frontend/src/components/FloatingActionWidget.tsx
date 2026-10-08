import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  MousePointer, 
  Keyboard as KeyboardIcon, 
  Minus, 
  GripHorizontal,
  Mouse,
  Lock,
  Unlock,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { Language, translations } from '../i18n';

interface FloatingActionWidgetProps {
  onLeftClick: () => void;
  onRightClick: () => void;
  onMouseDown: () => void;
  onMouseUp: () => void;
  onScroll: (dy: number) => void;
  onToggleKeyboard: () => void;
  isKeyboardOpen: boolean;
  lang: Language;
}

export const FloatingActionWidget: React.FC<FloatingActionWidgetProps> = ({
  onLeftClick,
  onRightClick,
  onMouseDown,
  onMouseUp,
  onScroll,
  onToggleKeyboard,
  isKeyboardOpen,
  lang,
}) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isHolding, setIsHolding] = useState(false);
  const widgetRef = useRef<HTMLDivElement | null>(null);
  const t = translations[lang];

  // Position reference
  const posRef = useRef<{ x: number; y: number }>({
    x: Math.max(10, window.innerWidth / 2 - 160),
    y: Math.max(10, window.innerHeight - 80),
  });

  const dragStartRef = useRef<{ startX: number; startY: number; initX: number; initY: number } | null>(null);

  // Viewport Boundary Clamping: Guarantees widgets NEVER get lost off-screen on rotate / fullscreen
  const clampPosition = useCallback(() => {
    const boundWidth = isMinimized ? 56 : 330;
    const boundHeight = isMinimized ? 56 : 65;
    
    const maxX = Math.max(8, window.innerWidth - boundWidth - 8);
    const maxY = Math.max(8, window.innerHeight - boundHeight - 8);

    const clampedX = Math.max(8, Math.min(maxX, posRef.current.x));
    const clampedY = Math.max(8, Math.min(maxY, posRef.current.y));

    posRef.current = { x: clampedX, y: clampedY };
    if (widgetRef.current) {
      widgetRef.current.style.transform = `translate3d(${clampedX}px, ${clampedY}px, 0)`;
    }
  }, [isMinimized]);

  useEffect(() => {
    clampPosition();
    window.addEventListener('resize', clampPosition);
    window.addEventListener('orientationchange', clampPosition);
    document.addEventListener('fullscreenchange', clampPosition);

    return () => {
      window.removeEventListener('resize', clampPosition);
      window.removeEventListener('orientationchange', clampPosition);
      document.removeEventListener('fullscreenchange', clampPosition);
    };
  }, [clampPosition]);

  const toggleHold = () => {
    if (isHolding) {
      onMouseUp();
      setIsHolding(false);
    } else {
      onMouseDown();
      setIsHolding(true);
    }
    if ('vibrate' in navigator) {
      try { navigator.vibrate(25); } catch (_) {}
    }
  };

  // Ultra-smooth GPU-accelerated drag handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    dragStartRef.current = {
      startX: touch.clientX,
      startY: touch.clientY,
      initX: posRef.current.x,
      initY: posRef.current.y,
    };
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!dragStartRef.current || !widgetRef.current) return;
    const touch = e.touches[0];
    const dx = touch.clientX - dragStartRef.current.startX;
    const dy = touch.clientY - dragStartRef.current.startY;

    const boundWidth = isMinimized ? 56 : 330;
    const boundHeight = isMinimized ? 56 : 65;

    const newX = Math.max(8, Math.min(window.innerWidth - boundWidth - 8, dragStartRef.current.initX + dx));
    const newY = Math.max(8, Math.min(window.innerHeight - boundHeight - 8, dragStartRef.current.initY + dy));

    posRef.current = { x: newX, y: newY };
    widgetRef.current.style.transform = `translate3d(${newX}px, ${newY}px, 0)`;
  };

  const handleTouchEnd = () => {
    dragStartRef.current = null;
  };

  if (isMinimized) {
    return (
      <div
        ref={widgetRef}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{
          transform: `translate3d(${posRef.current.x}px, ${posRef.current.y}px, 0)`,
          willChange: 'transform'
        }}
        className="fixed top-0 left-0 z-40 touch-none select-none"
      >
        <button
          onClick={() => setIsMinimized(false)}
          className={`w-13 h-13 rounded-full text-white shadow-2xl backdrop-blur-xl border-2 flex items-center justify-center p-3 active:scale-95 transition-transform ${
            isHolding 
              ? 'bg-rose-600 border-rose-400 ring-4 ring-rose-500/50 animate-pulse'
              : 'bg-indigo-600 border-indigo-400 shadow-indigo-500/50'
          }`}
          title="Tıklama Menüsünü Genişlet"
        >
          {isHolding ? <Lock className="w-6 h-6" /> : <Mouse className="w-6 h-6 animate-pulse" />}
        </button>
      </div>
    );
  }

  return (
    <div
      ref={widgetRef}
      style={{
        transform: `translate3d(${posRef.current.x}px, ${posRef.current.y}px, 0)`,
        willChange: 'transform'
      }}
      className="fixed top-0 left-0 z-40 touch-none select-none flex items-center bg-slate-900/90 backdrop-blur-2xl border border-slate-700/80 rounded-2xl p-1.5 shadow-2xl shadow-black/80 space-x-1"
    >
      {/* Draggable Handle */}
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className="px-1.5 py-3 cursor-grab active:cursor-grabbing text-slate-400 hover:text-white flex items-center justify-center active:scale-105"
        title="Sürükle ve Taşı"
      >
        <GripHorizontal className="w-4 h-4" />
      </div>

      {/* Sol Tık (Left Click) Button */}
      <button
        onClick={onLeftClick}
        className="px-3 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-400 text-white font-black text-xs rounded-xl flex items-center space-x-1 shadow-lg active:scale-95 transition"
      >
        <MousePointer className="w-3.5 h-3.5" />
        <span>{t.leftClick}</span>
      </button>

      {/* Sağ Tık (Right Click) Button */}
      <button
        onClick={onRightClick}
        className="px-3 py-2.5 bg-amber-500 hover:bg-amber-400 active:bg-amber-300 text-slate-950 font-black text-xs rounded-xl flex items-center space-x-1 shadow-lg active:scale-95 transition"
      >
        <MousePointer className="w-3.5 h-3.5" />
        <span>{t.rightClick}</span>
      </button>

      {/* HOLD / DRAG Button */}
      <button
        onClick={toggleHold}
        className={`px-2.5 py-2.5 font-black text-xs rounded-xl flex items-center space-x-1 transition active:scale-95 shadow-lg ${
          isHolding
            ? 'bg-rose-600 text-white ring-2 ring-rose-400 animate-pulse'
            : 'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700/60'
        }`}
        title={isHolding ? "Release Mouse Hold" : "Hold Left Mouse Button (Drag)"}
      >
        {isHolding ? <Lock className="w-3.5 h-3.5 text-white" /> : <Unlock className="w-3.5 h-3.5 text-slate-400" />}
        <span>{isHolding ? t.holdActive : t.hold}</span>
      </button>

      {/* Mini Scroll Up / Down Buttons */}
      <div className="flex flex-col gap-0.5">
        <button
          onClick={() => {
            onScroll(4.5);
            if ('vibrate' in navigator) try { navigator.vibrate(8); } catch (_) {}
          }}
          className="w-7 h-4 bg-slate-800 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 rounded flex items-center justify-center border border-slate-700/60 active:scale-95"
          title="Scroll Up"
        >
          <ChevronUp className="w-3 h-3" />
        </button>
        <button
          onClick={() => {
            onScroll(-4.5);
            if ('vibrate' in navigator) try { navigator.vibrate(8); } catch (_) {}
          }}
          className="w-7 h-4 bg-slate-800 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 rounded flex items-center justify-center border border-slate-700/60 active:scale-95"
          title="Scroll Down"
        >
          <ChevronDown className="w-3 h-3" />
        </button>
      </div>

      {/* Klavye (Keyboard) Button */}
      <button
        onClick={onToggleKeyboard}
        className={`p-2.5 rounded-xl transition active:scale-95 flex items-center justify-center ${
          isKeyboardOpen
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700/60'
        }`}
        title="Dahili Klavyeyi Aç/Kapat"
      >
        <KeyboardIcon className="w-4 h-4" />
      </button>

      {/* Minimize Button */}
      <button
        onClick={() => setIsMinimized(true)}
        className="p-1.5 text-slate-400 hover:text-white rounded-lg active:bg-slate-800 transition"
        title="Nokta Olarak Küçült"
      >
        <Minus className="w-4 h-4" />
      </button>
    </div>
  );
};
