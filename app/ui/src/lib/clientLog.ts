export async function reportClientError(opts: { message: string; stack?: string; extra?: Record<string, any> }) {
  try {
    const payload = {
      level: 'error',
      message: opts.message,
      stack: opts.stack,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      ui_version: (window as any).__UI_BUILD_VERSION || undefined,
      extra: opts.extra || {},
    }
    // Prefer alias path without /logs prefix to avoid router conflicts
    const res = await fetch('/api/v1/client-logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Correlation-Id': `UI-${Date.now()}` },
      body: JSON.stringify(payload),
      keepalive: true,
    })
    if (!res.ok) {
      const q = new URLSearchParams(Object.entries(payload).reduce((a, [k, v]) => { a[k] = String(v ?? ''); return a }, {} as Record<string, string>)).toString()
      await fetch(`/api/v1/client-logs?${q}`, { method: 'GET', headers: { 'X-Correlation-Id': `UI-${Date.now()}` } })
    }
  } catch {
    // swallow
  }
}

export function installGlobalClientErrorHooks() {
  if (typeof window === 'undefined') return
  if ((window as any).__ui_hooks_installed) return
  (window as any).__ui_hooks_installed = true
  window.addEventListener('error', (ev) => {
    try {
      const err: any = ev.error || ev.message
      reportClientError({ message: String(err?.message || err || 'window.onerror'), stack: String(err?.stack || '') })
    } catch { /* noop */ }
  })
  window.addEventListener('unhandledrejection', (ev: PromiseRejectionEvent) => {
    try {
      const reason: any = (ev && (ev as any).reason) || 'unhandledrejection'
      reportClientError({ message: String(reason?.message || reason), stack: String(reason?.stack || '') })
    } catch { /* noop */ }
  })
}
