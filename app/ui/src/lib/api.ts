// Lightweight API client with sane defaults for FeatureFactory UI
// Rules:
// - Prefix non-absolute, non-/api, non-/health, non-/.well-known paths with /api/v1
// - Inject X-Correlation-Id
// - JSON in/out with typed helpers

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface ApiResponse<T> {
  status: number
  data: T
}

function isAbsoluteUrl(url: string): boolean {
  return /^https?:\/\//i.test(url)
}

function shouldBypassPrefix(path: string): boolean {
  return path.startsWith('/api/') || path.startsWith('/health/') || path.startsWith('/.well-known/')
}

function withApiPrefix(path: string): string {
  if (!path.startsWith('/')) return `/api/v1/${path}`.replace(/\/+/g, '/').replace(/\/api\/v1\/api\//, '/api/')
  if (shouldBypassPrefix(path)) return path
  // Map legacy '/orchestrator/...' to '/api/v1/orchestrator/...'
  if (path.startsWith('/orchestrator/')) return `/api/v1${path}`
  return `/api/v1${path}`
}

function corrId(): string {
  const rnd = Math.random().toString(36).slice(2, 8)
  return `UI-${Date.now()}-${rnd}`
}

async function request<T>(method: HttpMethod, path: string, body?: any, init?: RequestInit): Promise<ApiResponse<T>> {
  const url = isAbsoluteUrl(path)
    ? path
    : withApiPrefix(path)

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'X-Correlation-Id': corrId(),
  }
  if (body !== undefined && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const resp = await fetch(url, {
    method,
    headers: { ...headers, ...(init?.headers as Record<string, string> | undefined) },
    body: body === undefined ? undefined : (body instanceof FormData ? body : JSON.stringify(body)),
    credentials: init?.credentials ?? 'same-origin',
    signal: init?.signal,
    mode: init?.mode,
  })

  const status = resp.status
  const text = await resp.text()
  let data: any
  try {
    data = text ? JSON.parse(text) : (undefined as unknown)
  } catch {
    // Fallback to plain text in case of non-JSON responses
    data = text as unknown
  }

  if (!resp.ok) {
    const msg = (data && (data.detail || data.message)) || `HTTP ${status}`
    throw new Error(typeof msg === 'string' ? msg : `HTTP ${status}`)
  }

  return { status, data: data as T }
}

export async function get<T>(path: string, init?: RequestInit): Promise<ApiResponse<T>> {
  return request<T>('GET', path, undefined, init)
}

export async function post<T = any>(path: string, body?: any, init?: RequestInit): Promise<ApiResponse<T>> {
  return request<T>('POST', path, body, init)
}

export async function put<T = any>(path: string, body?: any, init?: RequestInit): Promise<ApiResponse<T>> {
  return request<T>('PUT', path, body, init)
}

export async function del<T = any>(path: string, init?: RequestInit): Promise<ApiResponse<T>> {
  return request<T>('DELETE', path, undefined, init)
}

// No prefixing, pass-through helper
export async function getAbsolute<T>(url: string, init?: RequestInit): Promise<ApiResponse<T>> {
  return request<T>('GET', url, undefined, init)
}

