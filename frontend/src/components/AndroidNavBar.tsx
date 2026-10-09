import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  ArrowLeft, 
  Circle, 
  Square, 
  Power, 
  Volume1, 
  Volume2, 
  GripHorizontal, 
  Smartphone,
  ChevronDown
} from 'lucide-react';
import { Language, translations } from '../i18n';

interface AndroidNavBarProps {
  onNav: (action: 'back' | 'home' | 'recents' | 'power' | 'volume_up' | 'volume_down') => void;
  lang: Language;
}

export const AndroidNavBar: React.FC<AndroidNavBarProps> = ({ onNav, lang }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const t = translations[lang];
  const barRef = useRef<HTMLDivElement | null>(null);

  // Position reference (default pinned to bottom center)
  const posRef = useRef<{ x: number; y: number }>({
    x: Math.max(10, window.innerWidth / 2 - 140),
    y: Math.max(10, window.innerHeight - 56),
  });

  const dragStartRef = useRef<{ startX: number; startY: number; initX: number; initY: number } | null>(null);

  const clampPosition = useCallback(() => {
    const boundWidth = isMinimized ? 52 : 280;
    const boundHeight = 48;
    const maxX = Math.max(8, window.innerWidth - boundWidth - 8);
    const maxY = Math.max(8, window.innerHeight - boundHeight - 8);

    const clampedX = Math.max(8, Math.min(maxX, posRef.current.x));
    const clampedY = Math.max(8, Math.min(maxY, posRef.current.y));

    posRef.current = { x: clampedX, y: clampedY };
    if (barRef.current) {
      barRef.current.style.transform = `translate3d(${clampedX}px, ${clampedY}px, 0)`;
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

  const handlePointerDown = (clientX: number, clientY: number) => {
    dragStartRef.current = {
      startX: clientX,
      startY: clientY,
      initX: posRef.current.x,
      initY: posRef.current.y,
    };
  };

  const handlePointerMove = (clientX: number, clientY: number) => {
    if (!dragStartRef.current) return;
    const dx = clientX - dragStartRef.current.startX;
    const dy = clientY - dragStartRef.current.startY;
    posRef.current.x = dragStartRef.current.initX + dx;
    posRef.current.y = dragStartRef.current.initY + dy;
    clampPosition();
  };

  const handlePointerUp = () => {
    dragStartRef.current = null;
    clampPosition();
  };

  return (
    <div
      ref={barRef}
      style={{
        transform: `translate3d(${posRef.current.x}px, ${posRef.current.y}px, 0)`,
        touchAction: 'none',
      }}
      className="fixed top-0 left-0 z-40 select-none"
    >
      {isMinimized ? (
        <button
          onClick={() => setIsMinimized(false)}
          className="w-12 h-12 bg-slate-900/95 border border-indigo-500/50 rounded-2xl flex items-center justify-center text-indigo-400 shadow-2xl backdrop-blur-xl hover:bg-slate-800 active:scale-95 transition-transform"
          title={t.androidHome}
        >
          <Smartphone className="w-5 h-5" />
        </button>
      ) : (
        <div className="flex items-center space-x-1 p-1.5 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-2xl backdrop-blur-xl">
          {/* Drag Handle */}
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              handlePointerDown(e.clientX, e.clientY);
              const onMove = (me: MouseEvent) => handlePointerMove(me.clientX, me.clientY);
              const onUp = () => {
                handlePointerUp();
                window.removeEventListener('mousemove', onMove);
                window.removeEventListener('mouseup', onUp);
              };
              window.addEventListener('mousemove', onMove);
              window.addEventListener('mouseup', onUp);
            }}
            onTouchStart={(e) => {
              const t0 = e.touches[0];
              handlePointerDown(t0.clientX, t0.clientY);
            }}
            onTouchMove={(e) => {
              const t0 = e.touches[0];
              handlePointerMove(t0.clientX, t0.clientY);
            }}
            onTouchEnd={handlePointerUp}
            className="px-1.5 py-2 cursor-grab active:cursor-grabbing text-slate-500 hover:text-slate-300"
          >
            <GripHorizontal className="w-4 h-4" />
          </div>

          {/* Android Back Button */}
          <button
            onClick={() => onNav('back')}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 hover:text-white transition-colors"
            title={t.androidBack}
          >
            <ArrowLeft className="w-4 h-4" />
          </button>

          {/* Android Home Button */}
          <button
            onClick={() => onNav('home')}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 hover:text-white transition-colors"
            title={t.androidHome}
          >
            <Circle className="w-4 h-4" />
          </button>

          {/* Android Recents / App Switcher */}
          <button
            onClick={() => onNav('recents')}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-200 hover:text-white transition-colors"
            title={t.androidRecents}
          >
            <Square className="w-4 h-4" />
          </button>

          <div className="w-[1px] h-6 bg-slate-800 mx-0.5" />

          {/* Volume Down */}
          <button
            onClick={() => onNav('volume_down')}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-300 hover:text-white transition-colors"
            title={t.androidVolDown}
          >
            <Volume1 className="w-4 h-4" />
          </button>

          {/* Volume Up */}
          <button
            onClick={() => onNav('volume_up')}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 active:bg-indigo-600 text-slate-300 hover:text-white transition-colors"
            title={t.androidVolUp}
          >
            <Volume2 className="w-4 h-4" />
          </button>

          {/* Power Button */}
          <button
            onClick={() => onNav('power')}
            className="p-2.5 rounded-xl bg-rose-950/60 hover:bg-rose-900 border border-rose-800/50 text-rose-300 hover:text-white transition-colors"
            title={t.androidPower}
          >
            <Power className="w-4 h-4" />
          </button>

          {/* Minimize Button */}
          <button
            onClick={() => setIsMinimized(true)}
            className="p-2 text-slate-500 hover:text-slate-300 rounded-lg"
            title={t.minimize}
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
