/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Hardened WebSocket Client (Phase 23).
 */

export type WSConnectionState = 'CONNECTING' | 'LIVE' | 'RECONNECTING' | 'UNAVAILABLE';

export interface WSEnvelope {
  type: string;
  connection_id: string;
  sequence_number: number;
  timestamp: string;
  payload: any;
  ack_seq: number | null;
}

export type WSMessageCallback = (type: string, payload: any) => void;

/**
 * Safely inspect if a JWT token is expired without external dependencies.
 */
export function isTokenExpired(token: string | null | undefined): boolean {
  if (!token || token === "undefined" || token === "null" || token.trim() === "") return true;
  // Mock tokens used in tests or demo fixtures
  if (token.startsWith("mock-") || !token.includes(".")) return false;
  try {
    const parts = token.split(".");
    if (parts.length < 2) return false;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = typeof window !== "undefined" && window.atob
      ? decodeURIComponent(window.atob(base64).split("").map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)).join(""))
      : typeof Buffer !== "undefined"
      ? Buffer.from(base64, "base64").toString("utf-8")
      : "";
    if (!jsonPayload) return false;
    const payload = JSON.parse(jsonPayload);
    if (!payload.exp) return false;
    return Date.now() >= (payload.exp * 1000 - 5000);
  } catch {
    return false;
  }
}

class RealtimeClient {
  private socket: WebSocket | null = null;
  private url: string;
  private token: string;
  private state: WSConnectionState = 'UNAVAILABLE';
  private stateListeners: Set<(s: WSConnectionState) => void> = new Set();
  private messageListeners: Set<WSMessageCallback> = new Set();
  
  private connectionId: string | null = null;
  private outSeq: number = 0;
  private inSeq: number = -1;
  private unacked: Map<number, { type: string, payload: any, timestamp: number }> = new Map();
  
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private lastHeartbeat: number = Date.now();
  
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseBackoffMs = 1000;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  public setToken(newToken: string) {
    if (this.token !== newToken) {
      this.token = newToken;
      if (this.socket) {
        this.disconnect();
      }
      if (newToken && !isTokenExpired(newToken)) {
        this.reconnectAttempts = 0;
        this.connect();
      }
    }
  }

  public getToken(): string {
    return this.token;
  }

  public connect() {
    if (!this.token || isTokenExpired(this.token)) {
      this.updateState('UNAVAILABLE');
      return;
    }

    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      return;
    }
    
    this.updateState(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'CONNECTING');
    
    try {
      this.socket = new WebSocket(`${this.url}?token=${encodeURIComponent(this.token)}`);
      
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
    } catch (e) {
      console.warn('[DocAssistIQ WS] Error creating socket:', e);
      this.scheduleReconnect();
    }
  }

  public disconnect() {
    if (this.socket) {
      try {
        this.socket.close();
      } catch {
        // Ignored during shutdown
      }
      this.socket = null;
    }
    this.cleanup();
    this.updateState('UNAVAILABLE');
  }

  public send(type: string, payload: any = {}) {
    this.outSeq++;
    const msg = {
      type,
      connection_id: this.connectionId || '',
      sequence_number: this.outSeq,
      timestamp: new Date().toISOString(),
      payload,
      ack_seq: this.inSeq >= 0 ? this.inSeq : null
    };
    
    this.unacked.set(this.outSeq, { type, payload, timestamp: Date.now() });
    
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(msg));
    }
  }

  public subscribeState(callback: (s: WSConnectionState) => void) {
    this.stateListeners.add(callback);
    callback(this.state);
    return () => this.stateListeners.delete(callback);
  }

  public subscribeMessages(callback: WSMessageCallback) {
    this.messageListeners.add(callback);
    return () => this.messageListeners.delete(callback);
  }

  private handleOpen() {
    this.reconnectAttempts = 0;
    this.lastHeartbeat = Date.now();
    this.updateState('LIVE');
    this.startHeartbeat();
    
    // Resend unacked messages
    if (this.unacked.size > 0 && this.connectionId) {
      for (const [seq, msg] of this.unacked.entries()) {
        const resend = {
          type: msg.type,
          connection_id: this.connectionId,
          sequence_number: seq,
          timestamp: new Date().toISOString(),
          payload: msg.payload,
          ack_seq: this.inSeq >= 0 ? this.inSeq : null
        };
        this.socket?.send(JSON.stringify(resend));
      }
    }
  }

  private handleClose(event: CloseEvent) {
    console.warn(`[DocAssistIQ WS] Closed (code: ${event.code}, reason: "${event.reason || ''}")`);
    this.cleanup();
    
    // Auth failures (4001, 4003) or expired token shouldn't retry automatically
    if (event.code === 4001 || event.code === 4003 || isTokenExpired(this.token)) {
      this.updateState('UNAVAILABLE');
      return;
    }
    
    this.scheduleReconnect();
  }

  private handleError(event: Event) {
    // Native WebSocket 'error' events carry no diagnostic payload per W3C specification
    // and are always followed immediately by a 'close' event.
    // We log as warning instead of console.error to avoid triggering Next.js dev overlay popups.
    console.warn('[DocAssistIQ WS] Handshake notice (close event will follow):', event);
  }

  private handleMessage(event: MessageEvent) {
    this.lastHeartbeat = Date.now();
    
    try {
      const envelope: WSEnvelope = JSON.parse(event.data);
      
      // Process ACKs
      if (envelope.ack_seq !== null && envelope.ack_seq !== undefined) {
        // Clear all unacked messages up to ack_seq
        for (const seq of this.unacked.keys()) {
          if (seq <= envelope.ack_seq) {
            this.unacked.delete(seq);
          }
        }
      }
      
      // Duplicate suppression
      if (envelope.sequence_number <= this.inSeq) {
        console.debug('[DocAssistIQ WS] Duplicate message suppressed', envelope.sequence_number);
        return;
      }
      
      this.inSeq = envelope.sequence_number;
      
      if (envelope.type === 'connected') {
        this.connectionId = envelope.connection_id;
      } else if (envelope.type === 'heartbeat' || envelope.type === 'ping') {
        this.send('pong');
      } else if (envelope.type === 'pong') {
        // Just an ack, handled above
      } else {
        // Dispatch to business logic
        this.messageListeners.forEach(cb => cb(envelope.type, envelope.payload));
      }
      
    } catch (e) {
      console.warn('[DocAssistIQ WS] Malformed message ignored:', e);
    }
  }

  private startHeartbeat() {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = setInterval(() => {
      // Check if stale (45s threshold to accommodate local inference load)
      if (Date.now() - this.lastHeartbeat > 45000) {
        console.warn('[DocAssistIQ WS] Stale connection detected, resetting socket');
        this.socket?.close(4008);
      } else {
        this.send('heartbeat');
      }
    }, 10000);
  }

  private scheduleReconnect() {
    if (!this.token || isTokenExpired(this.token) || this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.updateState('UNAVAILABLE');
      return;
    }
    
    this.updateState('RECONNECTING');
    
    const delay = Math.min(this.baseBackoffMs * Math.pow(1.5, this.reconnectAttempts), 15000);
    this.reconnectAttempts++;
    
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private cleanup() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private updateState(newState: WSConnectionState) {
    if (this.state !== newState) {
      this.state = newState;
      this.stateListeners.forEach(cb => cb(newState));
    }
  }
}

// Singleton manager hook
let sharedClient: RealtimeClient | null = null;

export function getSharedRealtimeClient(token?: string | null): RealtimeClient {
  const safeToken = (token && token !== "undefined" && token !== "null") ? token.trim() : "";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "") ?? "http://localhost:8000";
  const wsUrl = apiBaseUrl.replace(/^http/, "ws") + "/ws/v1/stream";

  if (!sharedClient) {
    sharedClient = new RealtimeClient(wsUrl, safeToken);
    if (safeToken && !isTokenExpired(safeToken)) {
      sharedClient.connect();
    }
  } else if (safeToken && safeToken !== sharedClient.getToken()) {
    sharedClient.setToken(safeToken);
  }
  return sharedClient;
}

