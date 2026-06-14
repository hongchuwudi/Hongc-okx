/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: WebSocket 连接 — Redis Pub/Sub → 浏览器实时推送
 */

import type { WsEvent } from '@/types/ws'

type WsCallback = (event: WsEvent) => void

interface WsClient {
  close: () => void
  send: (data: string) => void
}

// 建立 WebSocket 连接到 /ws/v1/live，后端通过 Redis Pub/Sub 广播实时事件
// onEvent: 收到消息时的回调，消息类型包括:
//   - tick_complete: 每次 tick 完成后推送，含价格/权益/信号/持仓
//   - circuit_breaker: 熔断事件
// 返回 { close, send }，close 用于组件卸载时清理，send 用于心跳
// 内置 30 秒心跳保活，断线 3 秒后触发 ws_disconnected 事件通知调用方
export function connectWs(onEvent: WsCallback): WsClient {
  const host = import.meta.env.DEV ? 'localhost:8765' : location.host
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  let closed = false
  let ws: WebSocket | null = null

  // 延迟连接，避免 React StrictMode double-mount 导致立即关闭
  const timer = setTimeout(() => {
    if (closed) return
    const url = `${proto}//${host}/ws/v1/live`
    console.log(`[WS] connecting to ${url}`)
    ws = new WebSocket(url)

    ws.onopen = () => console.log('[WS] connected')

    ws.onmessage = (e) => {
      try { onEvent(JSON.parse(e.data) as WsEvent) } catch { /* ignore */ }
    }

    ws.onclose = (e) => {
      console.log(`[WS] closed code=${e.code} reason=${e.reason || 'none'}`)
      if (!closed) {
        setTimeout(() => {
          if (!closed) onEvent({ type: 'circuit_breaker', reason: 'ws_disconnected' })
        }, 3000)
      }
    }

    ws.onerror = () => {
      console.log('[WS] error')
      ws?.close()
    }
  }, 100)

  const ping = setInterval(() => {
    if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
  }, 30000)

  return {
    close: () => {
      closed = true
      clearTimeout(timer)
      clearInterval(ping)
      ws?.close()
    },
    send: (data: string) => {
      if (ws?.readyState === WebSocket.OPEN) ws.send(data)
    },
  }
}
