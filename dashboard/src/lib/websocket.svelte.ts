import { browser } from '$app/environment';

export interface ActionRecord {
    id: string;
    session_id: string;
    timestamp: string;
    type: string;
    description: string;
    domain: 'digital' | 'physical';
    was_guided: boolean;
    guidance_confidence: number | null;
}

export type ConnectionStatus = 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING';

export class WebSocketService {
    status = $state<ConnectionStatus>('DISCONNECTED');
    events = $state<ActionRecord[]>([]);
    
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectDelay = 10000;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private url: string;

    constructor(url: string = 'ws://127.0.0.1:8000/ws') {
        this.url = url;
    }

    connect() {
        if (!browser) return;
        
        if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        this.status = 'RECONNECTING';
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                this.status = 'CONNECTED';
                this.reconnectAttempts = 0;
                this.ws?.send('hello');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.event === 'action_logged') {
                        // Prepend to display newest first
                        this.events = [message.data, ...this.events];
                    }
                } catch (err) {
                    // Handshake or echo replies are text or other payloads
                }
            };

            this.ws.onclose = (event) => {
                if (this.status !== 'DISCONNECTED') {
                    this.status = 'DISCONNECTED';
                    this.ws = null;
                    this.scheduleReconnect();
                }
            };

            this.ws.onerror = (err) => {
                console.error('WebSocket error encountered:', err);
                this.status = 'DISCONNECTED';
            };
        } catch (e) {
            this.status = 'DISCONNECTED';
            this.scheduleReconnect();
        }
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.onclose = null;
            this.ws.close();
            this.ws = null;
        }
        this.status = 'DISCONNECTED';
    }

    private scheduleReconnect() {
        this.status = 'RECONNECTING';
        this.reconnectAttempts++;
        const delay = Math.min(
            this.maxReconnectDelay,
            1000 * Math.pow(1.5, this.reconnectAttempts) + Math.random() * 1000
        );
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }
}

export const wsService = new WebSocketService('ws://127.0.0.1:8000/ws');
