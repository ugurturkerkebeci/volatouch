import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Settings as SettingsIcon, 
  Maximize, 
  Minimize, 
  Crosshair, 
  Move, 
  ChevronUp,
  ChevronDown,
  Expand,
  Shrink
} from 'lucide-react';
import { ConnectionStatus } from '../types';

import { Language, translations } from '../i18n';

interface FloatingSettingsWidgetProps {
  onOpenSettings: () => void;
  inputMode: 'direct' | 'relative';
  onToggleInputMode: () => void;
  scaleMode: 'fit' | 'fill';
  onToggleScaleMode: () => void;
  status: ConnectionStatus;
  fps: number;
  latency?: number;
  lang: Language;
}

export const FloatingSettingsWidget: React.FC<FloatingSettingsWidgetProps> = ({
  onOpenSettings,
  inputMode,
  onToggleInputMode,
  scaleMode,
  onToggleScaleMode,
  status,
  fps,
  latency = 0,
  lang,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const widgetRef = useRef<HTMLDivElement | null>(null);
  const t = translations[lang];

  const posRef = useRef<{ x: number; y: number }>({
    x: 12,
    y: 12,
  });

  const isFullscreen = !!document.fullscreenElement;
  const dragStartRef = useRef<{ startX: number; startY: number; initX: number; initY: number } | null>(null);

  // Viewport Boundary Clamping on orientation change or fullscreen
  const clampPosition = useCallback(() => {
    const boundWidth = isCollapsed ? 75 : 240;
    const boundHeight = 44;

    const maxX = Math.max(8, window.innerWidth - boundWidth - 8);
    const maxY = Math.max(8, window.innerHeight - boundHeight - 8);

    const clampedX = Math.max(8, Math.min(maxX, posRef.current.x));
    const clampedY = Math.max(8, Math.min(maxY, posRef.current.y));

    posRef.current = { x: clampedX, y: clampedY };
    if (widgetRef.current) {
      widgetRef.current.style.transform = `translate3d(${clampedX}px, ${clampedY}px, 0)`;
    }
  }, [isCollapsed]);

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

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

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

    const boundWidth = isCollapsed ? 75 : 240;
    const boundHeight = 44;

    const newX = Math.max(8, Math.min(window.innerWidth - boundWidth - 8, dragStartRef.current.initX + dx));
    const newY = Math.max(8, Math.min(window.innerHeight - boundHeight - 8, dragStartRef.current.initY + dy));

    posRef.current = { x: newX, y: newY };
    widgetRef.current.style.transform = `translate3d(${newX}px, ${newY}px, 0)`;
  };

  const handleTouchEnd = () => {
    dragStartRef.current = null;
  };

  return (
    <div
      ref={widgetRef}
      style={{
        transform: `translate3d(${posRef.current.x}px, ${posRef.current.y}px, 0)`,
        willChange: 'transform'
      }}
      className="fixed top-0 left-0 z-40 touch-none select-none flex items-center bg-slate-900/90 backdrop-blur-xl border border-slate-700/80 rounded-full px-2 py-1 shadow-2xl space-x-1"
    >
      {/* Draggable Grip & Status Indicator */}
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className="flex items-center space-x-1.5 px-1 py-1 cursor-grab active:scale-105"
      >
        <span
          className={`w-2 h-2 rounded-full ${
            status === 'connected' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : 'bg-rose-500'
          }`}
        />
        <span className="text-[10px] font-mono text-emerald-400 font-bold">{fps}fps</span>
        {latency > 0 && (
          <span className="text-[10px] font-mono text-indigo-300 font-bold">{latency}ms</span>
        )}
      </div>

      {!isCollapsed && (
        <>
          <div className="w-px h-4 bg-slate-700 mx-0.5" />

          {/* Scale Mode Toggle (Fill Screen vs Fit Aspect Ratio) */}
          <button
            onClick={onToggleScaleMode}
            className={`px-2 py-1 rounded-full text-[11px] font-bold flex items-center space-x-1 transition active:scale-95 ${
              scaleMode === 'fill'
                ? 'bg-amber-600 text-white shadow'
                : 'bg-slate-800 text-slate-300 hover:text-white'
            }`}
            title="Toggle Screen Fill / Fit"
          >
            {scaleMode === 'fill' ? (
              <>
                <Expand className="w-3.5 h-3.5" />
                <span>{t.fillScreen}</span>
              </>
            ) : (
              <>
                <Shrink className="w-3.5 h-3.5" />
                <span>{t.fitScreen}</span>
              </>
            )}
          </button>

          {/* Mode Switch (Direct Target vs Relative Trackpad) */}
          <button
            onClick={onToggleInputMode}
            className={`px-2 py-1 rounded-full text-[11px] font-bold flex items-center space-x-1 transition active:scale-95 ${
              inputMode === 'direct'
                ? 'bg-indigo-600 text-white shadow'
                : 'bg-slate-800 text-slate-300 hover:text-white'
            }`}
            title="Toggle Input Mode"
          >
            {inputMode === 'direct' ? (
              <>
                <Crosshair className="w-3.5 h-3.5" />
                <span>{t.directTarget}</span>
              </>
            ) : (
              <>
                <Move className="w-3.5 h-3.5" />
                <span>{t.trackpad}</span>
              </>
            )}
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-full text-slate-300 hover:text-white active:bg-slate-800 transition"
            title="Tam Ekran Aç/Kapat"
          >
            {isFullscreen ? <Minimize className="w-3.5 h-3.5" /> : <Maximize className="w-3.5 h-3.5" />}
          </button>

          {/* Settings Modal Toggle */}
          <button
            onClick={onOpenSettings}
            className="p-1.5 rounded-full text-slate-300 hover:text-white active:bg-slate-800 transition"
            title="Ayarlar Menüsü"
          >
            <SettingsIcon className="w-3.5 h-3.5" />
          </button>
        </>
      )}

      {/* Collapse/Expand Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="p-1 text-slate-400 hover:text-white transition"
      >
        {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
      </button>
    </div>
  );
};
