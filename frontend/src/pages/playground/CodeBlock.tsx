/**
 * 创建时间: 2026-06-18
 * 作者: hongchuwudi
 * 描述: 源码展示组件 — highlight.js 语法高亮
 *
 * 包含:
 * - 组件: CodeBlock — 展示语法高亮的 TSX 源码
 */

import { useMemo } from 'react'
// highlight.js 作为 rehype-highlight 的依赖已安装
import hljs from 'highlight.js/lib/core'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'

// 仅注册需要的语言，减小体积
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('xml', xml)

interface Props {
  code: string
}

export default function CodeBlock({ code }: Props) {
  const html = useMemo(() => {
    const result = hljs.highlight(code, { language: 'typescript' })
    return result.value
  }, [code])

  return (
    <pre className="text-xs leading-relaxed p-4 overflow-x-auto whitespace-pre font-mono">
      <code
        className="language-typescript"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </pre>
  )
}
