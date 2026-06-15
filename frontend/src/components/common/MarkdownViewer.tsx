/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: Markdown 渲染组件 — 支持代码高亮、图片、链接、自适应宽度、可调字号
 */

import { useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'

interface Props {
  content: string
  fontSize?: number          // 默认 14px
}

export default function MarkdownViewer({ content, fontSize = 14 }: Props) {
  // 内联样式对象避免重复创建
  const style = useMemo(
    () => ({ fontSize: `${fontSize}px`, lineHeight: 1.75 }) as React.CSSProperties,
    [fontSize],
  )

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert" style={style}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          // 图片自适应容器宽度
          img: ({ src, alt }) => (
            <img src={src} alt={alt} className="max-w-full h-auto rounded-lg my-3" loading="lazy" />
          ),
          // 链接新窗口打开
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline">
              {children}
            </a>
          ),
          // 表格自适应滚动
          table: ({ children }) => (
            <div className="overflow-x-auto my-3">
              <table className="table table-sm table-zebra">{children}</table>
            </div>
          ),
          // 代码块无语言时默认显示
          pre: ({ children }) => (
            <pre className="rounded-lg !bg-base-200 !p-4 overflow-x-auto text-xs">{children}</pre>
          ),
          // 行内代码
          code: ({ className, children, ...props }) => {
            const isBlock = className?.startsWith('language-')
            if (isBlock) {
              return <code className={className} {...props}>{children}</code>
            }
            return <code className="badge badge-sm bg-base-200 text-base-content px-1 py-0 text-xs" {...props}>{children}</code>
          },
          // 引用块样式
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/30 pl-4 italic text-base-content/70 my-3">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
