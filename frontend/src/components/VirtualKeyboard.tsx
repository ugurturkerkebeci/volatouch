import React, { useState } from 'react';
import { 
  CornerDownLeft, 
  Delete as BackspaceIcon, 
  ChevronDown,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  SlidersHorizontal,
  Hash,
  Type,
  Mic
} from 'lucide-react';
import { ModifierKey } from '../types';
import { Language, translations } from '../i18n';

interface VirtualKeyboardProps {
  isOpen: boolean;
  onClose: () => void;
  onKeyTap: (key: string, modifiers?: string[]) => void;
  onTextInput: (text: string) => void;
  lang: Language;
}

export const VirtualKeyboard: React.FC<VirtualKeyboardProps> = ({
  isOpen,
  onClose,
  onKeyTap,
  onTextInput,
  lang,
}) => {
  const [activeModifiers, setActiveModifiers] = useState<Record<ModifierKey, boolean>>({
    ctrl: false,
    shift: false,
    alt: false,
    win: false,
  });

  const [activeTab, setActiveTab] = useState<'qwerty' | 'numbers' | 'fkeys' | 'text'>('qwerty');
  const [isCaps, setIsCaps] = useState(false);
  const [textInputValue, setTextInputValue] = useState('');
  const t = translations[lang];

  const isShifted = activeModifiers.shift || isCaps;

  const toggleModifier = (mod: ModifierKey) => {
    setActiveModifiers((prev) => ({
      ...prev,
      [mod]: !prev[mod],
    }));
    if ('vibrate' in navigator) {
      try { navigator.vibrate(12); } catch (_) {}
    }
  };

  const handleKeyClick = (key: string, isShiftVariant?: string) => {
    const mods = (Object.keys(activeModifiers) as ModifierKey[]).filter(
      (m) => activeModifiers[m]
    );

    let finalKey = key;

    // If shift or caps is active, resolve uppercase or symbol variant
    if (isShifted) {
      if (isShiftVariant) {
        finalKey = isShiftVariant;
      } else if (key.length === 1) {
        finalKey = key.toUpperCase();
      }
    } else {
      if (key.length === 1) {
        finalKey = key.toLowerCase();
      }
    }

    onKeyTap(finalKey, mods);

    // Auto-release Shift after single keypress (Standard mobile keyboard UX)
    if (activeModifiers.shift) {
      setActiveModifiers((prev) => ({ ...prev, shift: false }));
    }
    // Auto-release active modifiers after combo
    if (mods.length > 0) {
      setActiveModifiers({ ctrl: false, shift: false, alt: false, win: false });
    }

    if ('vibrate' in navigator) {
      try { navigator.vibrate(10); } catch (_) {}
    }
  };

  if (!isOpen) return null;

  // Key mappings for numbers and shift symbols
  const numberRow = [
    { base: '1', shift: '!' },
    { base: '2', shift: '@' },
    { base: '3', shift: '#' },
    { base: '4', shift: '$' },
    { base: '5', shift: '%' },
    { base: '6', shift: '^' },
    { base: '7', shift: '&' },
    { base: '8', shift: '*' },
    { base: '9', shift: '(' },
    { base: '0', shift: ')' },
  ];

  const qwertyRow1 = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'];
  const qwertyRow2 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'];
  const qwertyRow3 = ['z', 'x', 'c', 'v', 'b', 'n', 'm'];

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-slate-950/95 backdrop-blur-3xl border-t border-slate-800 shadow-2xl flex flex-col transition-all duration-200 select-none touch-none pb-safe max-h-[85vh]">
      {/* Top Header & Category Tabs */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70 shrink-0">
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setActiveTab('qwerty')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1 transition ${
              activeTab === 'qwerty' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-800'
            }`}
          >
            <Type className="w-3.5 h-3.5" />
            <span>{t.qwerty}</span>
          </button>
          <button
            onClick={() => setActiveTab('numbers')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1 transition ${
              activeTab === 'numbers' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-800'
            }`}
          >
            <Hash className="w-3.5 h-3.5" />
            <span>{t.symbols}</span>
          </button>
          <button
            onClick={() => setActiveTab('fkeys')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1 transition ${
              activeTab === 'fkeys' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-800'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{t.fkeys}</span>
          </button>
          <button
            onClick={() => setActiveTab('text')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1 transition ${
              activeTab === 'text' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-800'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>{t.voiceText}</span>
          </button>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition active:scale-90"
          title="Klavyeyi Kapat"
        >
          <ChevronDown className="w-5 h-5" />
        </button>
      </div>

      {/* PC Modifier Quick Strip */}
      <div className="grid grid-cols-6 gap-1 px-2 pt-2 shrink-0">
        {(['ctrl', 'alt', 'shift', 'win'] as ModifierKey[]).map((mod) => (
          <button
            key={mod}
            onClick={() => toggleModifier(mod)}
            className={`py-2 rounded-lg text-xs font-black uppercase transition active:scale-95 flex items-center justify-center ${
              activeModifiers[mod]
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/50 ring-2 ring-blue-300'
                : 'bg-slate-850 text-slate-300 bg-slate-800/90 border border-slate-700/60'
            }`}
          >
            {mod === 'win' ? '⊞ Win' : mod}
          </button>
        ))}
        <button
          onClick={() => handleKeyClick('esc')}
          className="py-2 rounded-lg text-xs font-bold uppercase bg-red-950/70 text-red-300 border border-red-900/60 active:bg-red-900 active:scale-95"
        >
          Esc
        </button>
        <button
          onClick={() => handleKeyClick('tab')}
          className="py-2 rounded-lg text-xs font-bold uppercase bg-slate-800/90 text-slate-300 border border-slate-700/60 active:bg-slate-700 active:scale-95"
        >
          Tab
        </button>
      </div>

      {/* TAB 1: OPTIMIZED FULL QWERTY KEYBOARD */}
      {activeTab === 'qwerty' && (
        <div className="p-2 space-y-1.5 overflow-y-auto">
          {/* Numbers / Shift-Symbols Row */}
          <div className="flex gap-1">
            {numberRow.map((item) => (
              <button
                key={item.base}
                onClick={() => handleKeyClick(item.base, item.shift)}
                className="flex-1 h-11 bg-slate-850 bg-slate-800/90 text-slate-100 text-sm font-black rounded-lg border border-slate-700/60 shadow-sm flex flex-col items-center justify-center active:bg-indigo-600 active:scale-95 transition"
              >
                <span>{isShifted ? item.shift : item.base}</span>
              </button>
            ))}
            <button
              onClick={() => handleKeyClick('backspace')}
              className="w-12 h-11 bg-slate-800 text-amber-400 rounded-lg flex items-center justify-center border border-slate-700/60 active:bg-amber-600 active:text-white active:scale-95 transition"
              title="Geri Sil"
            >
              <BackspaceIcon className="w-5 h-5" />
            </button>
          </div>

          {/* QWERTY Row 1 */}
          <div className="flex gap-1">
            {qwertyRow1.map((char) => (
              <button
                key={char}
                onClick={() => handleKeyClick(char)}
                className="flex-1 h-12 bg-slate-800/90 text-slate-100 text-base font-bold rounded-lg border border-slate-700/60 shadow-sm flex items-center justify-center active:bg-indigo-600 active:text-white active:scale-95 transition"
              >
                {isShifted ? char.toUpperCase() : char.toLowerCase()}
              </button>
            ))}
          </div>

          {/* QWERTY Row 2 */}
          <div className="flex gap-1 px-1.5">
            {qwertyRow2.map((char) => (
              <button
                key={char}
                onClick={() => handleKeyClick(char)}
                className="flex-1 h-12 bg-slate-800/90 text-slate-100 text-base font-bold rounded-lg border border-slate-700/60 shadow-sm flex items-center justify-center active:bg-indigo-600 active:text-white active:scale-95 transition"
              >
                {isShifted ? char.toUpperCase() : char.toLowerCase()}
              </button>
            ))}
            <button
              onClick={() => handleKeyClick('enter')}
              className="w-13 h-12 px-3 bg-indigo-600 text-white rounded-lg flex items-center justify-center active:bg-indigo-500 shadow-lg active:scale-95 transition"
              title="Enter"
            >
              <CornerDownLeft className="w-5 h-5 font-black" />
            </button>
          </div>

          {/* QWERTY Row 3 */}
          <div className="flex gap-1">
            {/* Caps Lock Toggle Button */}
            <button
              onClick={() => {
                setIsCaps(!isCaps);
                if ('vibrate' in navigator) {
                  try { navigator.vibrate(15); } catch (_) {}
                }
              }}
              className={`w-13 px-2 h-12 text-xs font-black rounded-lg border flex items-center justify-center space-x-1 active:scale-95 transition ${
                isCaps
                  ? 'bg-amber-600 text-white border-amber-400 ring-2 ring-amber-300 shadow-md'
                  : 'bg-slate-800 text-slate-400 border-slate-700/60'
              }`}
              title="Büyük / Küçük Harf Kilidi"
            >
              <div className={`w-1.5 h-1.5 rounded-full mr-1 ${isCaps ? 'bg-white animate-pulse' : 'bg-slate-600'}`} />
              <span>CAPS</span>
            </button>

            {qwertyRow3.map((char) => (
              <button
                key={char}
                onClick={() => handleKeyClick(char)}
                className="flex-1 h-12 bg-slate-800/90 text-slate-100 text-base font-bold rounded-lg border border-slate-700/60 shadow-sm flex items-center justify-center active:bg-indigo-600 active:text-white active:scale-95 transition"
              >
                {isShifted ? char.toUpperCase() : char.toLowerCase()}
              </button>
            ))}

            <button
              onClick={() => handleKeyClick('delete')}
              className="w-12 h-12 bg-slate-800 text-rose-300 text-xs font-bold rounded-lg border border-slate-700/60 active:bg-rose-700 active:scale-95 transition flex items-center justify-center"
            >
              DEL
            </button>
          </div>

          {/* Bottom Bar: Shortcuts + Space + Directional Arrows */}
          <div className="flex gap-1 pt-0.5">
            <button
              onClick={() => onKeyTap('c', ['ctrl'])}
              className="px-3 h-11 bg-slate-800 text-slate-200 text-xs font-mono font-bold rounded-lg border border-slate-700/60 active:bg-indigo-600 active:scale-95 transition"
            >
              Ctrl+C
            </button>
            <button
              onClick={() => onKeyTap('v', ['ctrl'])}
              className="px-3 h-11 bg-slate-800 text-slate-200 text-xs font-mono font-bold rounded-lg border border-slate-700/60 active:bg-indigo-600 active:scale-95 transition"
            >
              Ctrl+V
            </button>
            <button
              onClick={() => handleKeyClick('space')}
              className="flex-1 h-11 bg-slate-800 text-slate-200 text-sm font-black rounded-lg border border-slate-700/60 active:bg-slate-700 active:scale-95 transition flex items-center justify-center tracking-widest uppercase"
            >
              SPACE
            </button>
            <div className="flex gap-0.5">
              <button
                onClick={() => handleKeyClick('left')}
                className="w-9 h-11 bg-slate-800 text-slate-200 rounded-lg flex items-center justify-center active:bg-indigo-600 border border-slate-700/60 active:scale-95"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <div className="flex flex-col gap-0.5">
                <button
                  onClick={() => handleKeyClick('up')}
                  className="w-9 h-5 bg-slate-800 text-slate-200 rounded flex items-center justify-center active:bg-indigo-600 border border-slate-700/60 active:scale-95"
                >
                  <ArrowUp className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleKeyClick('down')}
                  className="w-9 h-5 bg-slate-800 text-slate-200 rounded flex items-center justify-center active:bg-indigo-600 border border-slate-700/60 active:scale-95"
                >
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
              </div>
              <button
                onClick={() => handleKeyClick('right')}
                className="w-9 h-11 bg-slate-800 text-slate-200 rounded-lg flex items-center justify-center active:bg-indigo-600 border border-slate-700/60 active:scale-95"
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SEMBOLLER */}
      {activeTab === 'numbers' && (
        <div className="p-3 grid grid-cols-5 gap-2 overflow-y-auto">
          {['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[', ']', '{', '}', ';', ':', '"', "'", '<', '>', '/', '?', '\\', '|', '~', '`'].map((sym) => (
            <button
              key={sym}
              onClick={() => handleKeyClick(sym)}
              className="h-12 bg-slate-800 hover:bg-slate-700 text-slate-100 text-lg font-black rounded-xl border border-slate-700/60 active:bg-indigo-600 active:scale-95 transition flex items-center justify-center"
            >
              {sym}
            </button>
          ))}
        </div>
      )}

      {/* TAB 3: F1-F12 FUNCTION KEYS */}
      {activeTab === 'fkeys' && (
        <div className="p-3 space-y-2 overflow-y-auto">
          <div className="grid grid-cols-4 gap-1.5">
            {Array.from({ length: 12 }, (_, i) => `f${i + 1}`).map((fKey) => (
              <button
                key={fKey}
                onClick={() => handleKeyClick(fKey)}
                className="h-11 bg-slate-800 hover:bg-slate-700 active:bg-indigo-600 text-slate-100 rounded-xl text-xs font-black uppercase tracking-wider border border-slate-700/60 active:scale-95 transition flex items-center justify-center"
              >
                {fKey.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-4 gap-1.5 pt-1">
            <button
              onClick={() => onKeyTap('tab', ['alt'])}
              className="py-2.5 bg-indigo-950/70 text-indigo-300 border border-indigo-800/60 rounded-xl text-xs font-bold active:bg-indigo-900 active:scale-95 transition"
            >
              Alt+Tab
            </button>
            <button
              onClick={() => onKeyTap('d', ['win'])}
              className="py-2.5 bg-indigo-950/70 text-indigo-300 border border-indigo-800/60 rounded-xl text-xs font-bold active:bg-indigo-900 active:scale-95 transition"
            >
              Win+D
            </button>
            <button
              onClick={() => onKeyTap('f4', ['alt'])}
              className="py-2.5 bg-rose-950/70 text-rose-300 border border-rose-800/60 rounded-xl text-xs font-bold active:bg-rose-900 active:scale-95 transition"
            >
              Alt+F4
            </button>
            <button
              onClick={() => onKeyTap('escape', ['ctrl', 'shift'])}
              className="py-2.5 bg-indigo-950/70 text-indigo-300 border border-indigo-800/60 rounded-xl text-xs font-bold active:bg-indigo-900 active:scale-95 transition"
            >
              {t.taskMgr}
            </button>
          </div>
        </div>
      )}

      {/* TAB 4: SES / METIN DOĞAL YAZMA */}
      {activeTab === 'text' && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (textInputValue.length > 0) {
              onTextInput(textInputValue);
              setTextInputValue('');
            }
          }}
          className="p-4 flex flex-col space-y-3"
        >
          <div className="flex space-x-2">
            <input
              type="text"
              value={textInputValue}
              onChange={(e) => setTextInputValue(e.target.value)}
              placeholder={t.typePlaceholder}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-bold transition active:scale-95 shadow-lg"
            >
              {t.send}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
