// Minimal SSE client with auto-reconnect and simple subscription API

type MessageListener = (event: MessageEvent<any>) => void
type GenericListener = (type: string, data: any, raw: MessageEvent<any>) => void

class SSEClient {
  private es: EventSource | null = null
  private url: string | null = null
  private messageListeners: Set<MessageListener> = new Set()
  private eventListeners: Map<string, Set<GenericListener>> = new Map()
  private anyListeners: Set<GenericListener> = new Set()
  private reconnectDelayMs = 1000
  private maxDelayMs = 5000

  connect(url: string): void {
    this.disconnect()
    this.url = url
    // Ensure API prefix if needed
    const fullUrl = url.startsWith('/api/') ? url : `/api/v1${url.startsWith('/') ? url : '/' + url}`
    const es = new EventSource(fullUrl)
    this.es = es

    es.onmessage = (ev) => {
      this.messageListeners.forEach((cb) => {
        try { cb(ev) } catch { /* ignore */ }
      })
      // Try to parse event data and dispatch to 'message' channel as generic too
      this.dispatchAny('message', this.parseData(ev.data), ev)
    }
    es.onerror = () => {
      this.scheduleReconnect()
    }

    // Rebind known typed listeners on fresh connection
    for (const [evt, listeners] of this.eventListeners.entries()) {
      if (listeners.size === 0) continue
      es.addEventListener(evt, (ev: MessageEvent<any>) => {
        const data = this.parseData(ev.data)
        this.dispatch(evt, data, ev)
      })
    }
  }

  on(cb: MessageListener): () => void {
    this.messageListeners.add(cb)
    return () => { this.messageListeners.delete(cb) }
  }

  onEvent(eventType: string, cb: GenericListener): () => void {
    if (!this.eventListeners.has(eventType)) this.eventListeners.set(eventType, new Set())
    const bucket = this.eventListeners.get(eventType)!
    bucket.add(cb)
    // If already connected, attach a listener for this event type once
    if (this.es) {
      this.es.addEventListener(eventType, (ev: MessageEvent<any>) => {
        const data = this.parseData(ev.data)
        this.dispatch(eventType, data, ev)
      })
    }
    return () => { bucket.delete(cb) }
  }

  onAny(cb: GenericListener): () => void {
    this.anyListeners.add(cb)
    return () => { this.anyListeners.delete(cb) }
  }

  disconnect(): void {
    if (this.es) {
      try { this.es.close() } catch { /* ignore */ }
      this.es = null
    }
  }

  private scheduleReconnect(): void {
    if (!this.url) return
    this.disconnect()
    const timeout = Math.min(this.reconnectDelayMs, this.maxDelayMs)
    setTimeout(() => {
      if (!this.url) return
      this.connect(this.url)
      this.reconnectDelayMs = Math.min(this.reconnectDelayMs * 2, this.maxDelayMs)
    }, timeout)
  }

  private parseData(raw: any): any {
    if (typeof raw !== 'string') return raw
    try { return JSON.parse(raw) } catch { return raw }
  }

  private dispatch(type: string, data: any, ev: MessageEvent<any>) {
    const bucket = this.eventListeners.get(type)
    if (bucket) bucket.forEach(cb => { try { cb(type, data, ev) } catch { /* ignore */ } })
    this.dispatchAny(type, data, ev)
  }

  private dispatchAny(type: string, data: any, ev: MessageEvent<any>) {
    this.anyListeners.forEach(cb => { try { cb(type, data, ev) } catch { /* ignore */ } })
  }
}

export const sseClient = new SSEClient()
