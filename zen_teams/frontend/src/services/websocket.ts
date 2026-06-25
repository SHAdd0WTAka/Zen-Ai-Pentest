const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/api/v1/ws/`

class WebSocketService {
  private ws: WebSocket | null = null
  private listeners: Map<string, Set<(payload: any) => void>> = new Map()
  private reconnectTimer: number | null = null
  private reconnectDelay = 3000

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(WS_URL)

    this.ws.onopen = () => {
      console.log('[WS] Connected')
      this.send({ action: 'subscribe', channel: 'all' })
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type && data.type !== 'ack') {
          this.emit(data.type, data.payload || data)
        }
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('[WS] Disconnected, reconnecting...')
      this.scheduleReconnect()
    }

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err)
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event: string, handler: (payload: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)
    return () => this.off(event, handler)
  }

  off(event: string, handler: (payload: any) => void) {
    this.listeners.get(event)?.delete(handler)
  }

  private emit(event: string, payload: any) {
    this.listeners.get(event)?.forEach((handler) => handler(payload))
    // Also emit to wildcard listeners
    this.listeners.get('*')?.forEach((handler) => handler({ event, payload }))
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, this.reconnectDelay)
  }
}

export const wsService = new WebSocketService()
