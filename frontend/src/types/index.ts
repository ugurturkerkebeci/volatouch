export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface StreamSettings {
  quality: number;      // 10 - 100
  scale: number;        // 0.3 - 1.0
}

export interface TouchpadSettings {
  sensitivity: number;        // 0.5 - 3.0
  acceleration: number;       // 0.0 - 0.05
  scrollSensitivity: number;  // 0.5 - 3.0
}

export interface SystemInfo {
  status: string;
  lan_ip: string;
  port: number;
  host_type?: 'windows' | 'android' | 'linux';
  screen: {
    width: number;
    height: number;
  };
  stream: {
    quality: number;
    scale: number;
    fps: number;
  };
}

export type ModifierKey = 'ctrl' | 'shift' | 'alt' | 'win';
