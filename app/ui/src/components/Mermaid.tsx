import React, { useEffect, useId, useRef } from 'react'

declare global { interface Window { mermaid?: any } }

const loadMermaid = async () => {
  if (window.mermaid) return window.mermaid
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Failed to load mermaid'))
    document.head.appendChild(s)
  })
  window.mermaid?.initialize?.({ startOnLoad: false, theme: 'default' })
  return window.mermaid
}

interface MermaidProps {
  chart: string
}

const Mermaid: React.FC<MermaidProps> = ({ chart }) => {
  const ref = useRef<HTMLDivElement>(null)
  const id = useId().replace(/:/g, '')

  useEffect(() => {
    let cancelled = false
    const render = async () => {
      try {
        const mermaid = await loadMermaid()
        const { svg } = await mermaid.render(`mermaid-${id}`, chart)
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('Mermaid render error', e)
      }
    }
    render()
    return () => { cancelled = true }
  }, [chart, id])

  return <div ref={ref} className="w-full overflow-auto" />
}

export default Mermaid
