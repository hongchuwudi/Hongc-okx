/**
 * 创建时间: 2026-06-18
 * 作者: hongchuwudi
 * 描述: 组件演练场 — 展示和调试公共组件
 */

import { useState } from 'react'
import FormSelect from '@/components/common/FormSelect'
import FormInput from '@/components/common/FormInput'
import FormCheck from '@/components/common/FormCheck'
import Dropdown from '@/components/common/Dropdown'
import Paginator from '@/components/common/Paginator'

import FormSelectRaw from '@/components/common/FormSelect.tsx?raw'
import FormInputRaw from '@/components/common/FormInput.tsx?raw'
import FormCheckRaw from '@/components/common/FormCheck.tsx?raw'
import DropdownRaw from '@/components/common/Dropdown.tsx?raw'
import PaginatorRaw from '@/components/common/Paginator.tsx?raw'
import ParamDrawerRaw from '@/pages/backtest/components/ParamDrawer.tsx?raw'

import hljs from 'highlight.js/lib/core'
import typescript from 'highlight.js/lib/languages/typescript'
hljs.registerLanguage('typescript', typescript)

function H({ code }: { code: string }) {
  const html = hljs.highlight(code, { language: 'typescript' }).value
  return <pre className="text-xs leading-relaxed p-4 overflow-x-auto font-mono whitespace-pre"><code dangerouslySetInnerHTML={{ __html: html }} /></pre>
}

export default function PlaygroundPage() {
  const [v, sv] = useState('opt1')
  const [t, st] = useState('')
  const [c, sc] = useState(false)
  const [g, sg] = useState(false)
  const [d, sd] = useState('sm')
  const [m, sm] = useState(false)

  const ROW = 'grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-base-300 border border-base-300 rounded-box overflow-hidden mb-3'

  return (
    <div className="p-6 space-y-3 h-[calc(100vh-4rem)] overflow-y-auto">
      <h2 className="text-lg font-bold mb-4">组件演练场</h2>

      {/* FormSelect */}
      <div className={ROW}>
        <div className="p-4 flex flex-wrap items-center gap-3">
          <FormSelect label="Label" size="sm" value={v} onChange={sv}
            options={[{ label:'Option 1', value:'opt1' },{ label:'Option 2', value:'opt2' }]} className="w-40" />
          <FormSelect size="sm" value={v} onChange={sv}
            options={[{ label:'No Label', value:'opt1' }]} className="w-32" />
        </div>
        <div className="bg-base-200"><H code={FormSelectRaw} /></div>
      </div>

      {/* FormInput */}
      <div className={ROW}>
        <div className="p-4 flex flex-wrap items-center gap-3">
          <FormInput label="Text" size="sm" value={t} onChange={st} placeholder="Type..." className="w-40" />
          <FormInput type="number" size="sm" value={t} onChange={st} className="w-28" />
        </div>
        <div className="bg-base-200"><H code={FormInputRaw} /></div>
      </div>

      {/* FormCheck */}
      <div className={ROW}>
        <div className="p-4 flex items-center gap-4">
          <FormCheck type="checkbox" size="sm" checked={c} onChange={sc} label="Checkbox" />
          <FormCheck type="toggle" size="sm" checked={g} onChange={sg} label="Toggle" />
        </div>
        <div className="bg-base-200"><H code={FormCheckRaw} /></div>
      </div>

      {/* Dropdown */}
      <div className={ROW}>
        <div className="p-4 flex items-center gap-3">
          <Dropdown size="sm" value={d} onChange={sd} placement="bottom"
            options={[{ label:'Down', value:'xs' },{ label:'Up', value:'sm' }]} />
          <Dropdown size="sm" value={d} onChange={sd} placement="top"
            options={[{ label:'Top', value:'xs' },{ label:'Sm', value:'sm' }]} />
        </div>
        <div className="bg-base-200"><H code={DropdownRaw} /></div>
      </div>

      {/* Paginator */}
      <div className={ROW}>
        <div className="p-4">
          <Paginator current={3} total={200} pageSize={20} pageSizeOptions={[10,20,50]} showSizeChanger />
        </div>
        <div className="bg-base-200"><H code={PaginatorRaw} /></div>
      </div>

      {/* Buttons */}
      <div className="border border-base-300 rounded-box overflow-hidden mb-3">
        <div className="px-4 py-2 bg-base-200 border-b border-base-300 text-sm font-semibold">Buttons</div>
        <div className="p-4 flex flex-wrap gap-2">
          <button className="btn btn-soft">Default</button>
          <button className="btn btn-soft btn-primary">Primary</button>
          <button className="btn btn-soft btn-secondary">Secondary</button>
          <button className="btn btn-soft btn-accent">Accent</button>
          <button className="btn btn-soft btn-info">Info</button>
          <button className="btn btn-soft btn-success">Success</button>
          <button className="btn btn-soft btn-warning">Warning</button>
          <button className="btn btn-soft btn-error">Error</button>
        </div>
      </div>

      {/* Modal */}
      <div className={ROW}>
        <div className="p-4 flex items-center">
          <button className="btn btn-primary btn-sm" onClick={() => sm(true)}>Open Modal</button>
          {m && (
            <dialog open className="modal modal-open">
              <div className="modal-box">
                <form method="dialog">
                  <button type="button" onClick={() => sm(false)} className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">X</button>
                </form>
                <h3 className="font-bold text-lg">Modal Title</h3>
                <p className="py-4 text-sm text-base-content/70">Click backdrop or X to close.</p>
                <div className="modal-action">
                  <button className="btn btn-sm" onClick={() => sm(false)}>Close</button>
                </div>
              </div>
              <form method="dialog" className="modal-backdrop">
                <button type="button" onClick={() => sm(false)}>close</button>
              </form>
            </dialog>
          )}
        </div>
        <div className="bg-base-200"><H code={ParamDrawerRaw} /></div>
      </div>
    </div>
  )
}
