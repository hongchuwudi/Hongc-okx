/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: HTTP 请求拦截器 — 统一处理 baseURL、JSON 解析、错误拦截
 */

const BASE = '/api/v1'

// 拦截器配置
interface InterceptorConfig {
  onRequest?: (url: string, init: RequestInit) => RequestInit
  onResponse?: <T>(data: T) => T
  onError?: (err: unknown) => never
}

let _config: InterceptorConfig = {}

// 注册拦截器
export function setupInterceptor(cfg: InterceptorConfig) {
  _config = cfg
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let reqInit = { ...init }

  if (_config.onRequest) {
    reqInit = _config.onRequest(`${BASE}${path}`, reqInit)
  }

  const res = await fetch(`${BASE}${path}`, reqInit)

  if (!res.ok) {
    // 尝试从 JSON 响应中提取后端错误消息，失败则用原始文本
    let msg: string
    try {
      const json = await res.json()
      msg = json?.error || json?.detail || ''
    } catch {
      msg = await res.text().catch(() => '')
    }
    const err = new Error(msg || `服务器错误 (${res.status})`)
    if (_config.onError) return _config.onError(err)
    throw err
  }

  const data = await res.json() as T

  if (_config.onResponse) {
    return _config.onResponse(data)
  }

  return data
}

// DELETE 请求
export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' })
}

// GET 请求
export function get<T>(path: string): Promise<T> {
  return request<T>(path)
}

// POST 请求
export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
}

// PUT 请求
export function put<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
