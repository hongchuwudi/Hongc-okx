/**
 * CDP 调试脚本 — 连接 Chrome 收集控制台错误（不关闭用户标签页）
 * 用法: node scripts/cdp-check.js [/path]
 */
const TARGET = process.argv[2] || '/logs'

async function go() {
  const listText = await fetch('http://127.0.0.1:9222/json').then(r => r.text()).catch(() => '')
  const pages = safeJson(listText)
  if (!pages) { console.error('无法连接 CDP'); process.exit(1) }

  // 找已有 localhost:5173 标签页，找不到才新建
  let page = pages.find(p => p.url?.includes('localhost:5173'))
  let created = false
  if (page) {
    console.log('[复用]', page.id, page.url.slice(0, 50))
  } else {
    const newText = await fetch(
      `http://127.0.0.1:9222/json/new?url=http://localhost:5173${TARGET}`,
      { method: 'PUT' }
    ).then(r => r.text()).catch(() => '')
    page = safeJson(newText)
    if (!page) { console.error('新建标签页失败'); process.exit(1) }
    created = true
    console.log('[新建]', page.id)
  }

  const ws = new WebSocket(page.webSocketDebuggerUrl)
  const bad = []
  const errs = []
  let id = 1
  const cb = new Map()

  ws.onmessage = (e) => {
    const m = safeJson(e.data)
    if (!m) return
    if (m.id && cb.has(m.id)) { cb.get(m.id)(m.result); cb.delete(m.id); return }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params?.exceptionDetails
      bad.push(`[${d?.lineNumber}:${d?.columnNumber}] ${d?.text || d?.exception?.description}  --  ${(d?.url||'').replace(/.*\/src\//,'src/')}`)
    }
    if (m.method === 'Runtime.consoleAPICalled' && m.params?.type === 'error') {
      errs.push(m.params.args.map(a => a.value ?? a.description ?? '?').join(' '))
    }
  }

  await new Promise(r => ws.onopen = r)

  function send(method, params) {
    return new Promise(resolve => {
      const cid = id++
      cb.set(cid, resolve)
      ws.send(JSON.stringify({ id: cid, method, params }))
    })
  }

  await send('Page.enable')
  await send('Runtime.enable')

  if (created) {
    // 新建的标签页需要导航
    await send('Page.navigate', { url: `http://localhost:5173${TARGET}` })
  } else {
    // 已有的标签页做硬刷新，拿到最新代码
    await send('Page.reload', { ignoreCache: true })
    // 如果 URL 不是目标路径，再导航
    if (!page.url.includes(TARGET)) {
      await send('Page.navigate', { url: `http://localhost:5173${TARGET}` })
    }
  }

  await new Promise(r => setTimeout(r, 4000))
  ws.close()

  // 如果新建了标签页，检查完关掉不留空白
  if (created) {
    await fetch(`http://127.0.0.1:9222/json/close/${page.id}`).catch(() => {})
  }

  console.log('')
  if (!bad.length && !errs.length) {
    console.log(TARGET + '  无 JS 错误')
  } else {
    if (bad.length) console.log('--- 未捕获异常 ---\n' + bad.join('\n'))
    if (errs.length) console.log('--- console.error ---\n' + errs.join('\n'))
  }
}

function safeJson(s) { try { return JSON.parse(s) } catch { return null } }

go().catch(e => { console.error('FATAL:', e.message); process.exit(1) })
