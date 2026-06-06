import { useEffect, useRef } from 'react'

export function useAutoRefresh(
  callback: () => void,
  enabled: boolean,
  intervalMs = 10000,
) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return
    const id = setInterval(() => savedCallback.current(), intervalMs)
    return () => clearInterval(id)
  }, [enabled, intervalMs])
}
