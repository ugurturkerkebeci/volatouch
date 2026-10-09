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
  // Scale Mode: 'fit' for Android Phone (maintain phone aspect ratio), 'fill' for PC
  const [scaleMode, setScaleMode] = useState<'fit' | 'fill'>('fit');
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showAndroidPermTip, setShowAndroidPermTip] = useState(true);

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
          if (data.host_type === 'android') {
            setScaleMode('fit');
          } else {
            setScaleMode('fill');
          }
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

      {/* ANDROID SCREEN CAPTURE PERMISSION HELPER OVERLAY */}
      {hostType === 'android' && streamStatus === 'connected' && fps === 0 && showAndroidPermTip && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 max-w-md w-11/12 p-4 bg-slate-900/95 border border-amber-500/60 rounded-2xl shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-top-4">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
              ⚠️
            </div>
            <div className="flex-1 text-xs sm:text-sm">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-100">
                  {lang === 'tr' ? 'Android Ekran Erişimi (Rootsuz)' : 'Android Screen Access (Zero-Root)'}
                </h4>
                <button
                  onClick={() => setShowAndroidPermTip(false)}
                  className="text-slate-400 hover:text-slate-200 text-xs px-2 py-0.5 rounded bg-slate-800"
                >
                  ✕
                </button>
              </div>
              <p className="text-slate-300 mt-1 leading-relaxed">
                {lang === 'tr'
                  ? 'Android güvenlik politikası nedeniyle Termux\'ta ekran yakalamak ve dokunmatik kontrol için Root OLMADAN şu yöntemleri kullanabilirsiniz:'
                  : 'Android security restricts background screencap. To stream without Root, use any of these methods:'}
              </p>
              <div className="mt-2 p-2 bg-slate-950/80 rounded-lg font-mono text-[11px] text-amber-300 space-y-1.5 border border-slate-800">
                <div>⚡ 1. Kablosuz Debug (Rootsuz): <code className="text-white font-bold">pkg install android-tools && adb connect localhost:&lt;port&gt;</code></div>
                <div>⚡ 2. Shizuku (Rootsuz): <code className="text-white font-bold">rish -c volatouch</code></div>
                <div>⚡ 3. PC'den USB/Wi-Fi: <code className="text-white font-bold">adb shell volatouch</code></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ANDROID SYSTEM NAVIGATION BAR (Shown cleanly when host is Android phone) */}
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

      {/* YÜZEN TIKLAMA VE KLAVYE ADASI (Yalnızca Telefondan PC kontrol edilirken gösterilir) */}
      {hostType !== 'android' && (
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
      )}

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
