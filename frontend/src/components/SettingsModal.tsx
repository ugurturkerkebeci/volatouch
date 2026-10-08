import React from 'react';
import { X, Maximize, Minimize, Sliders, Monitor, Cpu, Languages } from 'lucide-react';
import { StreamSettings, TouchpadSettings, ConnectionStatus } from '../types';
import { Language, translations } from '../i18n';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  streamSettings: StreamSettings;
  onUpdateStreamSettings: (s: Partial<StreamSettings>) => void;
  touchSettings: TouchpadSettings;
  onUpdateTouchSettings: (t: Partial<TouchpadSettings>) => void;
  status: ConnectionStatus;
  fps: number;
  lang: Language;
  onLanguageChange: (lang: Language) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  streamSettings,
  onUpdateStreamSettings,
  touchSettings,
  onUpdateTouchSettings,
  status,
  fps,
  lang,
  onLanguageChange,
}) => {
  const isFullscreen = !!document.fullscreenElement;
  const t = translations[lang];

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.warn('Fullscreen request failed:', err);
      });
    } else {
      document.exitFullscreen().catch((err) => {
        console.warn('Exit fullscreen failed:', err);
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md overflow-hidden"
    >
      <div className="w-full max-w-sm max-h-[85vh] sm:max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Sticky Header with prominent, touch-friendly close button */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/90 backdrop-blur shrink-0 z-10">
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-100">{t.settings}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white bg-slate-800/80 active:bg-slate-700 transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 overscroll-contain">
          {/* Language Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Languages className="w-3.5 h-3.5" />
              <span>{t.language}</span>
            </label>
            <div className="grid grid-cols-2 gap-2 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => onLanguageChange('en')}
                className={`py-2 text-xs font-bold rounded-lg transition-all ${
                  lang === 'en'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => onLanguageChange('tr')}
                className={`py-2 text-xs font-bold rounded-lg transition-all ${
                  lang === 'tr'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Türkçe
              </button>
            </div>
          </div>

          {/* Diagnostics Card */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  status === 'connected' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-400">{t.status}:</span>
              <span className="font-semibold text-slate-200 capitalize">{status}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-400">{t.streamFps}:</span>
              <span className="font-semibold text-emerald-400 font-mono">{fps} FPS</span>
            </div>
          </div>

          {/* Stream Settings */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center space-x-1">
              <Monitor className="w-3.5 h-3.5" />
              <span>Display Stream</span>
            </h3>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{t.streamQuality}</span>
                <span className="font-mono text-indigo-300">{streamSettings.quality}%</span>
              </div>
              <input
                type="range"
                min={15}
                max={95}
                step={5}
                value={streamSettings.quality}
                onChange={(e) => onUpdateStreamSettings({ quality: Number(e.target.value) })}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{t.resolutionScale}</span>
                <span className="font-mono text-indigo-300">{Math.round(streamSettings.scale * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.3}
                max={1.0}
                step={0.05}
                value={streamSettings.scale}
                onChange={(e) => onUpdateStreamSettings({ scale: Number(e.target.value) })}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>
          </div>

          {/* Trackpad Settings */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Trackpad
            </h3>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{t.cursorSpeed}</span>
                <span className="font-mono text-indigo-300">{touchSettings.sensitivity.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min={0.5}
                max={3.0}
                step={0.1}
                value={touchSettings.sensitivity}
                onChange={(e) => onUpdateTouchSettings({ sensitivity: Number(e.target.value) })}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{t.acceleration}</span>
                <span className="font-mono text-indigo-300">{touchSettings.acceleration > 0 ? 'On' : 'Off'}</span>
              </div>
              <input
                type="range"
                min={0.0}
                max={0.03}
                step={0.005}
                value={touchSettings.acceleration}
                onChange={(e) => onUpdateTouchSettings({ acceleration: Number(e.target.value) })}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>
          </div>

          {/* Fullscreen Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={toggleFullscreen}
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 border border-slate-700/60 rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition"
            >
              {isFullscreen ? (
                <>
                  <Minimize className="w-4 h-4 text-indigo-400" />
                  <span>{t.exitFullscreen}</span>
                </>
              ) : (
                <>
                  <Maximize className="w-4 h-4 text-indigo-400" />
                  <span>{t.goFullscreen}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Modal Footer with quick Close button */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/90 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="w-full py-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-bold transition active:scale-[0.98]"
          >
            {lang === 'tr' ? 'Kapat / Tamam' : 'Done / Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
