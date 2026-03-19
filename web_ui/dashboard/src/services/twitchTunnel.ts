// ============================================
// Twitch Chat Tunnel - Frontend Client
// ============================================
// Receives API responses through Twitch chat!

interface TunnelRequest {
  id: string;
  type: 'request';
  method: string;
  path: string;
  body?: any;
}

interface TunnelResponse {
  id: string;
  type: 'response';
  status: number;
  data?: any;
  error?: string;
}

type EventCallback = (data?: any) => void;

export class TwitchChatClient {
  private ws: WebSocket | null = null;
  private channel: string;
  private nickname: string;
  private token: string;
  private connected = false;

  // Message reassembly
  private receiveBuffer: Map<string, string[]> = new Map();
  private pendingRequests: Map<string, { resolve: Function; reject: Function }> = new Map();

  // Event handlers
  private eventHandlers: Map<string, EventCallback[]> = new Map();

  constructor(channel: string, nickname: string, token: string) {
    this.channel = channel.toLowerCase().replace('#', '');
    this.nickname = nickname;
    this.token = token;
  }

  on(event: string, callback: EventCallback) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)?.push(callback);
  }

  emit(event: string, data?: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(callback => callback(data));
    }
  }

  removeAllListeners() {
    this.eventHandlers.clear();
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Connect to Twitch IRC via WebSocket
      this.ws = new WebSocket('wss://irc-ws.chat.twitch.tv:443');

      this.ws.onopen = () => {
        console.log('🟢 Connected to Twitch IRC');

        // Authenticate
        this.ws?.send(`PASS ${this.token}`);
        this.ws?.send(`NICK ${this.nickname}`);

        // Request capabilities
        this.ws?.send('CAP REQ :twitch.tv/tags twitch.tv/commands');

        // Join channel
        this.ws?.send(`JOIN #${this.channel}`);
      };

      this.ws.onmessage = (event) => {
        const lines = event.data.split('\r\n');

        for (const line of lines) {
          if (!line) continue;

          // Handle PING
          if (line.startsWith('PING')) {
            this.ws?.send('PONG :tmi.twitch.tv');
            continue;
          }

          // Handle successful connection
          if (line.includes('001') && line.includes(this.nickname)) {
            this.connected = true;
            console.log(`✅ Joined #${this.channel}`);
            this.emit('connected');
            resolve();
          }

          // Handle PRIVMSG
          if (line.includes('PRIVMSG')) {
            this.handlePrivmsg(line);
          }
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('🔴 Disconnected from Twitch');
        this.connected = false;
        this.emit('disconnected');
      };
    });
  }

  private handlePrivmsg(line: string): void {
    // Parse IRC PRIVMSG
    const msgMatch = line.match(/PRIVMSG\s+#\w+\s+:(.+)$/);
    if (!msgMatch) return;

    const message = msgMatch[1];

    // Check if it's a tunnel message
    if (!message.startsWith('!zen|')) return;

    const parts = message.split('|');
    if (parts.length !== 5) return;

    const [, id, seqStr, totalStr, data] = parts;
    const seq = parseInt(seqStr);
    const total = parseInt(totalStr);

    // Reassemble message
    if (!this.receiveBuffer.has(id)) {
      this.receiveBuffer.set(id, new Array(total).fill(null));
    }

    const buffer = this.receiveBuffer.get(id)!;
    buffer[seq] = data;

    // Check if complete
    if (buffer.every(chunk => chunk !== null)) {
      const fullData = buffer.join('');
      this.receiveBuffer.delete(id);

      // Decode
      try {
        const decoded = atob(fullData);
        const jsonData = JSON.parse(decoded);

        console.log('📨 Received:', jsonData.type);
        this.handleMessage(jsonData);
      } catch (e) {
        console.error('Failed to decode message:', e);
      }
    }
  }

  private handleMessage(data: any): void {
    // Handle different message types
    if (data.type === 'response') {
      const pending = this.pendingRequests.get(data.id);
      if (pending) {
        if (data.error) {
          pending.reject(new Error(data.error));
        } else {
          pending.resolve(data);
        }
        this.pendingRequests.delete(data.id);
      }
    } else if (data.type === 'server_ready') {
      console.log('🚀 Server ready! Routes:', data.routes);
      this.emit('serverReady', data.routes);
    }

    this.emit('message', data);
  }

  async request(method: string, path: string, body?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.connected || !this.ws) {
        reject(new Error('Not connected'));
        return;
      }

      const id = Math.random().toString(36).substring(7);

      const request: TunnelRequest = {
        id,
        type: 'request',
        method,
        path,
        body
      };

      // Store pending request
      this.pendingRequests.set(id, { resolve, reject });

      // Send request (via chat - we need to encode it)
      const jsonStr = JSON.stringify(request);
      const encoded = btoa(jsonStr);

      // Split into chunks (Twitch limit ~500 chars)
      const chunkSize = 400;
      const chunks: string[] = [];
      for (let i = 0; i < encoded.length; i += chunkSize) {
        chunks.push(encoded.slice(i, i + chunkSize));
      }

      // Send chunks with delay (rate limit)
      chunks.forEach((chunk, index) => {
        setTimeout(() => {
          const msg = `!zen|${id}|${index}|${chunks.length}|${chunk}`;
          this.ws?.send(`PRIVMSG #${this.channel} :${msg}`);
        }, index * 1500); // 1.5s delay between chunks
      });

      console.log(`📤 ${method} ${path} (${chunks.length} chunks)`);

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Request timeout'));
        }
      }, 30000);
    });
  }

  // Convenience methods
  async get(path: string): Promise<any> {
    return this.request('GET', path);
  }

  async post(path: string, body: any): Promise<any> {
    return this.request('POST', path, body);
  }

  disconnect(): void {
    this.ws?.close();
  }
}

// Export singleton
export const twitchClient = new TwitchChatClient(
  import.meta.env.VITE_TWITCH_CHANNEL || '',
  import.meta.env.VITE_TWITCH_NICK || 'zen_user',
  import.meta.env.VITE_TWITCH_TOKEN || ''
);
