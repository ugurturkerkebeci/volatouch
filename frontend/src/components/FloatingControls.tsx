import React from 'react';
import { Keyboard, Settings, Move } from 'lucide-react';
import { ConnectionStatus } from '../types';

interface FloatingControlsProps {
  onToggleKeyboard: () => void;
  onToggleSettings: () => void;
  isKeyboardOpen: boolean;
  isDragging: boolean;
  status: ConnectionStatus;
}

export const FloatingControls: React.FC<FloatingControlsProps> = ({
  onToggleKeyboard,
  onToggleSettings,
  isKeyboardOpen,
  isDragging,
  status,
}) => {
  return (
    <div className="absolute top-3 right-3 z-30 flex items-center space-x-2 select-none">
      {/* Drag & Drop active banner */}
      {isDragging && (
        <div className="bg-amber-500/90 text-slate-950 font-bold text-[11px] px-2.5 py-1 rounded-full flex items-center space-x-1 shadow-lg animate-pulse">
          <Move className="w-3 h-3" />
          <span>DRAGGING</span>
        </div>
      )}

      {/* Floating control buttons */}
      <div className="flex items-center bg-slate-900/80 backdrop-blur-md border border-slate-700/60 rounded-full p-1 shadow-xl">
        {/* Keyboard Button */}
        <button
          onClick={onToggleKeyboard}
          className={`p-2 rounded-full transition ${
            isKeyboardOpen
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-300 hover:text-white active:bg-slate-800'
          }`}
          title="Toggle PC Keyboard"
        >
          <Keyboard className="w-4 h-4" />
        </button>

        {/* Settings Button */}
        <button
          onClick={onToggleSettings}
          className="p-2 rounded-full text-slate-300 hover:text-white active:bg-slate-800 transition"
          title="Stream & Trackpad Settings"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* Connection status indicator */}
        <div className="px-2 flex items-center">
          <span
            className={`w-2 h-2 rounded-full ${
              status === 'connected'
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                : status === 'connecting'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
        </div>
      </div>
    </div>
  );
};
