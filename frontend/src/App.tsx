import React, { useState, useEffect } from 'react';
import { useStreamSocket } from './hooks/useStreamSocket';
import { useTouchEngine } from './hooks/useTouchEngine';
import { ScreenCanvas } from './components/ScreenCanvas';
import { VirtualKeyboard } from './components/VirtualKeyboard';
import { SettingsModal } from './components/SettingsModal';
import { FloatingActionWidget } from './components/FloatingActionWidget';
import { FloatingSettingsWidget } from './components/FloatingSettingsWidget';
import { AndroidNavBar } from './components/AndroidNavBar';
import { StreamSettings, TouchpadSettings } from './types';
import { Language } from './i18n';

export const App: React.FC = () => {
  const serverHost = window.location.host || 'localhost:8000';

  const [lang, setLang] = useState<Language>(() => {
    const saved = localStorage.getItem('volatouch_lang');
    return (saved === 'en' || saved === 'tr') ? (saved as Language) : 'en';
  });

  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem('volatouch_lang', newLang);
  };

  const [hostType, setHostType] = useState<'windows' | 'android' | 'linux'>('windows');

  const [streamSettings, setStreamSettings] = useState<StreamSettings>({
    quality: 60,
    scale: 0.7,
  });

  const [touchSettings, setTouchSettings] = useState<TouchpadSettings>({
    sensitivity: 1.4,
    acceleration: 0.012,
    scrollSensitivity: 1.2,
  });

  // Input Mode: 'direct' (Tap navigates cursor directly to point) | 'relative' (Trackpad style)
  const [inputMode, setInputMode] = useState<'direct' | 'relative'>('direct');
  // Scale Mode: 'fill' (Stretches to 100% of mobile display without black bars) | 'fit' (Aspect Ratio Contain)
  const [scaleMode, setScaleMode] = useState<'fit' | 'fill'>('fill');
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Binary stream socket
  const {
    status: streamStatus,
    fps,
    latency,
    updateSettings: updateRemoteStreamSettings,
    currentBitmapRef,
  } = useStreamSocket({
    serverHost,
    initialSettings: streamSettings,
  });

  // Touch & hardware control engine
  const {
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    sendMouseMoveAbs,
    sendMouseClick,
    sendMouseDown,
    sendMouseUp,
    sendScroll,
    sendKeyTap,
    sendTextInput,
    sendAndroidNav,
  } = useTouchEngine({
    serverHost,
    settings: touchSettings,
  });

  // Detect server host type (Windows PC vs Android Phone)
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    fetch(`${protocol}//${serverHost}/api/info`)
      .then((res) => res.json())
      .then((data) => {
        if (data?.host_type) {
          setHostType(data.host_type);
        }
      })
      .catch(() => {});
  }, [serverHost]);

  // Physical desktop keyboard sync (typing on PC keyboard sends keystrokes/text to target)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || isKeyboardOpen) {
        return;
      }

      if (e.key === 'Backspace') {
        sendKeyTap('backspace');
        e.preventDefault();
      } else if (e.key === 'Enter') {
        sendKeyTap('enter');
        e.preventDefault();
      } else if (e.key === 'Escape') {
        if (hostType === 'android') {
          sendAndroidNav('back');
        } else {
          sendKeyTap('esc');
        }
        e.preventDefault();
      } else if (e.key === 'ArrowUp') {
        sendKeyTap('up');
        e.preventDefault();
      } else if (e.key === 'ArrowDown') {
        sendKeyTap('down');
        e.preventDefault();
      } else if (e.key === 'ArrowLeft') {
        sendKeyTap('left');
        e.preventDefault();
      } else if (e.key === 'ArrowRight') {
        sendKeyTap('right');
        e.preventDefault();
      } else if (e.key === 'Tab') {
        sendKeyTap('tab');
        e.preventDefault();
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        sendTextInput(e.key);
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hostType, isKeyboardOpen, sendKeyTap, sendTextInput, sendAndroidNav]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-950 select-none touch-none text-slate-100">
      {/* 100% Screen Video Canvas - Fully responsive in Portrait & Landscape */}
      <ScreenCanvas
        currentBitmapRef={currentBitmapRef}
        status={streamStatus}
        fps={fps}
        inputMode={inputMode}
        scaleMode={scaleMode}
        hostType={hostType}
        onDirectMove={(normX, normY) => sendMouseMoveAbs(normX, normY)}
        onRelativeTouchStart={handleTouchStart}
        onRelativeTouchMove={handleTouchMove}
        onRelativeTouchEnd={handleTouchEnd}
        onMouseDown={sendMouseDown}
        onMouseUp={sendMouseUp}
        onMouseClick={sendMouseClick}
        onScroll={sendScroll}
        onAndroidNav={sendAndroidNav}
      />

      {/* ANDROID SYSTEM NAVIGATION BAR (Shown when host is Android phone) */}
      {hostType === 'android' && (
        <AndroidNavBar
          onNav={sendAndroidNav}
          lang={lang}
        />
      )}

      {/* YÜZEN AYAR VE SİSTEM ÇUBUĞU (Bağımsız, taşınabilir ve küçültülebilir) */}
      <FloatingSettingsWidget
        onOpenSettings={() => setIsSettingsOpen(true)}
        inputMode={inputMode}
        onToggleInputMode={() => setInputMode((prev) => (prev === 'direct' ? 'relative' : 'direct'))}
        scaleMode={scaleMode}
        onToggleScaleMode={() => setScaleMode((prev) => (prev === 'fill' ? 'fit' : 'fill'))}
        status={streamStatus}
        fps={fps}
        latency={latency}
        lang={lang}
      />

      {/* YÜZEN TIKLAMA VE KLAVYE ADASI (Sol Tık, Sağ Tık, Hold, Scroll, Klavye) */}
      <FloatingActionWidget
        onLeftClick={() => sendMouseClick('left')}
        onRightClick={() => sendMouseClick('right')}
        onMouseDown={() => sendMouseDown('left')}
        onMouseUp={() => sendMouseUp('left')}
        onScroll={(dy) => sendScroll(dy)}
        onToggleKeyboard={() => setIsKeyboardOpen((prev) => !prev)}
        isKeyboardOpen={isKeyboardOpen}
        lang={lang}
      />

      {/* DAHİLİ TAM QWERTY SANAL KLAVYE */}
      <VirtualKeyboard
        isOpen={isKeyboardOpen}
        onClose={() => setIsKeyboardOpen(false)}
        onKeyTap={sendKeyTap}
        onTextInput={sendTextInput}
        lang={lang}
      />

      {/* AYARLAR MODALI */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        streamSettings={streamSettings}
        onUpdateStreamSettings={(newVals) => {
          setStreamSettings((prev) => ({ ...prev, ...newVals }));
          updateRemoteStreamSettings(newVals);
        }}
        touchSettings={touchSettings}
        onUpdateTouchSettings={(newVals) => {
          setTouchSettings((prev) => ({ ...prev, ...newVals }));
        }}
        status={streamStatus}
        fps={fps}
        lang={lang}
        onLanguageChange={handleLanguageChange}
      />
    </div>
  );
};

export default App;
